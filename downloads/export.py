import json
import os
import csv

from decimal import Decimal
from os import path, makedirs
from django.conf import settings
from django.shortcuts import get_object_or_404
from sys import modules
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.utils.text import slugify

from experiments.models import Experiment, Group, Participant, EEGData, EMGData, EEGSetting, EMGSetting, TMSData, \
    TMSSetting, AdditionalData, ContextTree, GenericDataCollectionData, GoalkeeperGameData, Step, \
    QuestionnaireResponse, Questionnaire, EEG, EMG, TMS, GoalkeeperGame, Stimulus, EMGElectrodeSetting, \
    EEGElectrodePosition, EMGSurfacePlacement, EMGIntramuscularPlacement, EMGNeedlePlacement, QuestionnaireLanguage, \
    QuestionnaireDefaultLanguage

DEFAULT_LANGUAGE = "pt-BR"

input_data_keys = [
    "base_directory",
    "export_per_participant",
    "export_per_questionnaire",
    "per_participant_directory",
    "per_questionnaire_directory",
    "export_filename",
    "questionnaire_list"
]

classification_of_disease_fields = [
    {"field": 'code', "header": 'code', "description": _("Code")},
    {"field": 'description', "header": 'description', "description": _("Description")},
    {"field": 'abbreviated_description', "header": 'abbreviated_description', "description": _(
        "Abbreviated description")},
]


def save_to_csv(complete_filename, rows_to_be_saved):
    """
    :param complete_filename: filename and directory structure where file is going to be saved
    :param rows_to_be_saved: list of rows that are going to be written on the file
    :return:
    """
    with open(complete_filename.encode('utf-8'), 'w', newline='', encoding='UTF-8') as csv_file:
        export_writer = csv.writer(csv_file, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        for row in rows_to_be_saved:
            export_writer.writerow(row)


def create_directory(basedir, path_to_create):
    """
    Create a directory

    :param basedir: directory that already exists (parent path where new path must be included)
    :param path_to_create: directory to be created
    :return:
            - "" if path was correctly created or error message if there was an error
            - complete_path -> basedir + path created
    """

    complete_path = ""

    if not path.exists(basedir.encode('utf-8')):
        return "Base path does not exist", complete_path

    complete_path = path.join(basedir, path_to_create)

    if not path.exists(complete_path.encode('utf-8')):
        makedirs(complete_path.encode('utf-8'))

    return "", complete_path


class ExportExecution:
    def get_username(self, request):
        self.user_name = None
        if request.user.is_authenticated():
            self.user_name = request.user.username
        return self.user_name

    def set_directory_base(self, export_id):
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT + '/download')):
            os.makedirs(os.path.join(settings.MEDIA_ROOT + '/download'))
        self.directory_base = path.join(
            self.base_directory_name, str(export_id)
        )

    def get_directory_base(self):

        return self.directory_base  # MEDIA_ROOT/temp/export_id

    def __init__(self, export_id):
        self.files_to_zip_list = []
        self.directory_base = ''
        self.base_directory_name = path.join(settings.MEDIA_ROOT, "download")
        self.set_directory_base(export_id)
        self.base_export_directory = ""
        self.user_name = None
        self.input_data = {}
        self.per_participant_data = {}
        self.per_participant_data_from_experiment = {}
        self.participants_per_entrance_questionnaire = {}
        self.participants_per_experiment_questionnaire = {}
        self.questionnaires_data = {}
        self.questionnaires_experiment_data = {}
        self.questionnaires_experiment_responses = {}
        self.root_directory = ""
        self.participants_filtered_data = []
        self.questionnaire_code_and_id = {}
        self.per_group_data = {}

    def read_configuration_data(self, json_file, update_input_data=True):
        json_data = open(json_file)

        input_data_temp = json.load(json_data)

        if update_input_data:
            self.input_data = input_data_temp

        json_data.close()

        return input_data_temp

    def is_input_data_consistent(self):

        # verify if important tags from input_data are available
        for data_key in input_data_keys:
            # if not self.get_input_data(data_key):
            if data_key not in self.input_data.keys():
                return False
        return True

    def create_export_directory(self):

        base_directory = self.get_input_data("base_directory")

        error_msg, self.base_export_directory = create_directory(
            self.get_directory_base(), base_directory
        )

        return error_msg

    def get_input_data(self, key):

        if key in self.input_data.keys():
            return self.input_data[key]
        return ""

    def get_export_directory(self):
        # /MEDIA_ROOT/download/experiment_id/
        return self.directory_base

    def process_experiment_data(self, experiment_id):
        """
        General experiment data
        :param experiment_id: Experiment object id
        :return:
        """
        error_msg = ""
        experiment = get_object_or_404(Experiment, pk=experiment_id)

        study = experiment.study
        experiment_resume_header = [
            'study', 'study_description', 'start_date', 'end_date',
            'experiment_title', 'experiment_description'
        ]

        experiment_resume = [
            study.title, study.description, str(study.start_date),
            str(study.end_date), experiment.title, experiment.description
        ]

        filename_experiment_resume = "%s.csv" % "Experiment"

        # path ex. /EXPERIMENT_DOWNLOAD/
        export_experiment_data = self.get_input_data("base_directory")

        # path ex. /media/download/experiment_id/
        experiment_resume_directory = self.get_export_directory()
        # /media/download/experiment_id/Experiment.csv
        complete_filename_experiment_resume = path.join(
            experiment_resume_directory, filename_experiment_resume
        )

        experiment_description_fields = []
        experiment_description_fields.insert(0, experiment_resume_header)
        experiment_description_fields.insert(1, experiment_resume)
        save_to_csv(
            complete_filename_experiment_resume, experiment_description_fields
        )

        self.files_to_zip_list.append(
            [complete_filename_experiment_resume, export_experiment_data]
        )

        # process data for each group
        group_list = Group.objects.filter(experiment=experiment)
        for group in group_list:
            group_resume = "Group name: " + group.title + "\n" + \
                           "Group description: " + group.description + "\n"
            group_directory_name = 'Group_' + slugify(group.title)

            error_msg, group_directory = create_directory(
                experiment_resume_directory, group_directory_name
            )
            if error_msg != "":
                return error_msg
            export_directory_group = path.join(
                export_experiment_data, group_directory_name
            )

            if hasattr(group, 'experimental_protocol'):
                # If there's no minimal data in ExperimentalProtocol model
                # do not create Experimental Protocol subdir
                if not group.experimental_protocol.textual_description\
                        and not group.experimental_protocol.image:
                    continue

                # build diseases inclusion criteria
                if group.inclusion_criteria.all():
                    group_inclusion_criteria_list = \
                        self.process_group_inclusion_disease(
                            group.inclusion_criteria.all()
                        )

                    group_inclusion_disease_filename = \
                        "%s.csv" % "Group_inclusion_criteria_disease"
                    # /download/experiment_id/Group_x/Group_inclusion_disease.csv
                    complete_inclusion_disease_filename = \
                        path.join(
                            group_directory, group_inclusion_disease_filename
                        )
                    # save personal_data_list to csv file
                    save_to_csv(
                        complete_inclusion_disease_filename,
                        group_inclusion_criteria_list
                    )
                    self.files_to_zip_list.append(
                        [complete_inclusion_disease_filename,
                         export_directory_group]
                    )

                # /download/experiment_id/Group_x/Experimental_protocol
                error_msg, directory_experimental_protocol = \
                    create_directory(group_directory, "Experimental_protocol")
                if error_msg != "":
                    return error_msg

                export_directory_experimental_protocol = \
                    path.join(export_directory_group, "Experimental_protocol")

                # save experimental protocol description
                experimental_protocol_description = \
                    group.experimental_protocol.textual_description
                if experimental_protocol_description:
                    filename_experimental_protocol = \
                        "%s.txt" % "Experimental_protocol_description"
                    # EXPERIMENT_DOWNLOAD/Group_x/Experimental_protocol
                    # /Experimental_protocol_description.txt
                    complete_filename_experimental_protocol = \
                        path.join(
                            directory_experimental_protocol,
                            filename_experimental_protocol
                        )

                    self.files_to_zip_list.append(
                        [complete_filename_experimental_protocol,
                         export_directory_experimental_protocol]
                    )

                    with open(
                            complete_filename_experimental_protocol.encode(
                                'utf-8'
                            ), 'w', newline='', encoding='UTF-8') as txt_file:
                        txt_file.writelines(group_resume)
                        txt_file.writelines(experimental_protocol_description)

                # save protocol image
                if hasattr(group.experimental_protocol, "image"):
                    experimental_protocol_image_filename = \
                        group.experimental_protocol.image.name
                    filename_protocol_image = "Experimental_protocol_image.png"
                    complete_protocol_image_filename = \
                        path.join(
                            directory_experimental_protocol,
                            filename_protocol_image
                        )
                    self.files_to_zip_list.append(
                        [complete_protocol_image_filename,
                         export_directory_experimental_protocol]
                    )

                    image_protocol = path.join(
                        path.join(settings.BASE_DIR, "media/"),
                        experimental_protocol_image_filename
                    )
                    with open(image_protocol, 'rb') as f:
                        data = f.read()

                    with open(complete_protocol_image_filename, 'wb') as f:
                        f.write(data)

                # By each step of the Experimental protocol -
                # export default setting
                questionnaire_setting_list = Step.objects.filter(
                    group=group, type='questionnaire'
                )
                for questionnaire_step in questionnaire_setting_list:
                    questionnaire_step_name = \
                        "STEP_" + questionnaire_step.numeration + "_" + \
                        questionnaire_step.type.upper()
                    path_questionnaire_directory = path.join(
                        directory_experimental_protocol,
                        questionnaire_step_name
                    )
                    if not path.exists(path_questionnaire_directory):
                        error_msg, path_questionnaire_directory = \
                            create_directory(
                                directory_experimental_protocol,
                                questionnaire_step_name
                            )
                        if error_msg != "":
                            return error_msg

                    export_questionnaire_directory = path.join(
                        export_directory_experimental_protocol,
                        questionnaire_step_name
                    )
                    self.export_experimental_protocol_additional_files(
                        questionnaire_step, path_questionnaire_directory,
                        export_questionnaire_directory
                    )

                eeg_setting_list = Step.objects.filter(group=group, type='eeg')
                for eeg_step in eeg_setting_list:
                    # create directory of eeg step
                    eeg_step_name = "STEP_" + eeg_step.numeration + "_" + eeg_step.type.upper()
                    path_eeg_directory = path.join(directory_experimental_protocol, eeg_step_name)
                    if not path.exists(path_eeg_directory):
                        error_msg, path_eeg_directory = create_directory(directory_experimental_protocol, eeg_step_name)
                        if error_msg != "":
                            return error_msg

                    export_eeg_directory = path.join(export_directory_experimental_protocol, eeg_step_name)
                    if hasattr(eeg_step, 'eeg'):
                        default_eeg = get_object_or_404(EEG, pk=eeg_step.id)
                        eeg_default_setting_description = get_eeg_setting_description(default_eeg.eeg_setting.id)
                        if eeg_default_setting_description:
                            eeg_setting_filename = "%s.json" % "eeg_default_setting"
                            # TODO:
                            # bug: fails if path exists. See "if not
                            # path.exists" above
                            complete_filename_eeg_setting = path.join(path_eeg_directory, eeg_setting_filename)

                            self.files_to_zip_list.append([complete_filename_eeg_setting, export_eeg_directory])

                            with open(complete_filename_eeg_setting.encode('utf-8'), 'w', newline='',
                                      encoding='UTF-8') as outfile:
                                json.dump(eeg_default_setting_description, outfile, indent=4)

                    # additional files
                    self.export_experimental_protocol_additional_files(eeg_step, path_eeg_directory,
                                                                       export_eeg_directory)

                emg_setting_list = Step.objects.filter(group=group, type='emg')
                for emg_step in emg_setting_list:
                    # create directory of emg step
                    emg_step_name = "STEP_" + emg_step.numeration + "_" + emg_step.type.upper()
                    path_emg_directory = path.join(directory_experimental_protocol, emg_step_name)
                    if not path.exists(path_emg_directory):
                        error_msg, path_emg_directory = create_directory(directory_experimental_protocol, emg_step_name)
                        if error_msg != "":
                            return error_msg

                    export_emg_directory = path.join(export_directory_experimental_protocol, emg_step_name)

                    if hasattr(emg_step, 'emg'):
                        default_emg = get_object_or_404(EMG, pk=emg_step.id)
                        emg_default_setting_description = get_emg_setting_description(default_emg.emg_setting.id)
                        if emg_default_setting_description:
                            emg_setting_filename = "%s.json" % "emg_default_setting"
                            complete_filename_emg_setting = path.join(path_emg_directory, emg_setting_filename)

                            self.files_to_zip_list.append([complete_filename_emg_setting, export_emg_directory])

                            with open(complete_filename_emg_setting.encode('utf-8'), 'w', newline='',
                                      encoding='UTF-8') as outfile:
                                json.dump(emg_default_setting_description, outfile, indent=4)

                    # additional files
                    self.export_experimental_protocol_additional_files(emg_step, path_emg_directory,
                                                                       export_emg_directory)

                tms_setting_list = Step.objects.filter(group=group, type='tms')
                for tms_step in tms_setting_list:
                    # create directory of tms step
                    tms_step_name = "STEP_" + tms_step.numeration + "_" + tms_step.type.upper()
                    path_tms_directory = path.join(directory_experimental_protocol, tms_step_name)
                    if not path.exists(path_tms_directory):
                        error_msg, path_tms_directory = create_directory(directory_experimental_protocol, tms_step_name)
                        if error_msg != "":
                            return error_msg

                    export_tms_directory = path.join(export_directory_experimental_protocol, tms_step_name)

                    if hasattr(tms_step, 'tms'):
                        default_tms = get_object_or_404(TMS, pk=tms_step.id)
                        tms_default_setting_description = get_tms_setting_description(default_tms.tms_setting.id)
                        if tms_default_setting_description:
                            tms_setting_filename = "%s.json" % "tms_default_setting"
                            complete_filename_tms_setting = path.join(path_tms_directory, tms_setting_filename)

                            self.files_to_zip_list.append([complete_filename_tms_setting, export_tms_directory])

                            with open(complete_filename_tms_setting.encode('utf-8'), 'w', newline='',
                                      encoding='UTF-8') as outfile:
                                json.dump(tms_default_setting_description, outfile, indent=4)

                    # additional files
                    self.export_experimental_protocol_additional_files(tms_step, path_tms_directory,
                                                                       export_tms_directory)

                goalkeeper_game_list = Step.objects.filter(group=group, type='goalkeeper_game')
                for goalkeeper_game_step in goalkeeper_game_list:
                    default_goalkeeper_game = get_object_or_404(GoalkeeperGame, pk=goalkeeper_game_step.id)

                    context_tree_default_description = get_context_tree_description(
                        default_goalkeeper_game.context_tree.id)
                    if context_tree_default_description:
                        # create directory of goalkeeper_game step
                        goalkeeper_game_step_name = "STEP_" + goalkeeper_game_step.numeration + "_" + \
                                                    goalkeeper_game_step.type.upper()

                        path_goalkeeper_game_directory = path.join(directory_experimental_protocol,
                                                                   goalkeeper_game_step_name)
                        if not path.exists(path_goalkeeper_game_directory):
                            error_msg, path_goalkeeper_game_directory = create_directory(directory_experimental_protocol,
                                                                                         goalkeeper_game_step_name)
                            if error_msg != "":
                                return error_msg

                        export_goalkeeper_game_directory = path.join(export_directory_experimental_protocol,
                                                                          goalkeeper_game_step_name)

                        goalkeeper_game_setting_filename = "%s.json" % "goalkeeper_game_default_setting"
                        complete_filename_goalkeeper_game_setting = path.join(path_goalkeeper_game_directory,
                                                                              goalkeeper_game_setting_filename)

                        self.files_to_zip_list.append([complete_filename_goalkeeper_game_setting,
                                                       export_goalkeeper_game_directory])

                        with open(complete_filename_goalkeeper_game_setting.encode('utf-8'), 'w', newline='',
                                  encoding='UTF-8') as outfile:
                            json.dump(context_tree_default_description, outfile, indent=4)

                        # if context_tree have a file
                        setting_file = default_goalkeeper_game.context_tree.setting_file if \
                            default_goalkeeper_game.context_tree.setting_file else ''
                        if setting_file:
                            context_tree_file = setting_file.file if setting_file.file else ''
                            if context_tree_file:
                                saved_context_tree_filename = context_tree_file.name
                                read_filename_context_tree = path.join(settings.MEDIA_ROOT, saved_context_tree_filename)
                                context_tree_filename = saved_context_tree_filename.split('/')[-1]
                                complete_context_tree_filename = path.join(path_goalkeeper_game_directory,
                                                                           context_tree_filename)

                                with open(read_filename_context_tree, "rb") as f:
                                    data = f.read()
                                with open(complete_context_tree_filename, "wb") as f:
                                    f.write(data)

                                self.files_to_zip_list.append([complete_context_tree_filename,
                                                               export_goalkeeper_game_directory])

                    # additional files
                    self.export_experimental_protocol_additional_files(goalkeeper_game_step,
                                                                       path_goalkeeper_game_directory,
                                                                       export_goalkeeper_game_directory)

                stimulus_list = Step.objects.filter(group=group, type='stimulus')
                for stimulus_step in stimulus_list:
                    stimulus = get_object_or_404(Stimulus, pk=stimulus_step.id)
                    if stimulus.media_file:
                        stimulus_step_name = "STEP_" + stimulus_step.numeration + "_" + stimulus_step.type.upper()
                        path_stimulus_directory = path.join(directory_experimental_protocol, stimulus_step_name)
                        if not path.exists(path_stimulus_directory):
                            error_msg, path_stimulus_directory = create_directory(directory_experimental_protocol,
                                                                                  stimulus_step_name)
                            if error_msg != "":
                                return error_msg

                        export_stimulus_directory = path.join(export_directory_experimental_protocol,
                                                                   stimulus_step_name)

                        stimulus_setting_filename = stimulus.media_file.name.split('/')[-1]
                        complete_stimulus_filename = path.join(path_stimulus_directory, stimulus_setting_filename)
                        read_stimulus_filename = path.join(settings.MEDIA_ROOT, stimulus.media_file.name)

                        with open(read_stimulus_filename, "rb") as f:
                            data = f.read()
                        with open(complete_stimulus_filename, "wb") as f:
                            f.write(data)

                        self.files_to_zip_list.append([complete_stimulus_filename, export_stimulus_directory])

                        # additional files
                        self.export_experimental_protocol_additional_files(stimulus_step, path_stimulus_directory,
                                                                           export_stimulus_directory)

                generic_data_collection_list = Step.objects.filter(group=group, type='generic_data_collection')
                for generic_data_step in generic_data_collection_list:
                    # generic_data_collection = get_object_or_404(GenericDataCollectionData,
                    #                                             pk=generic_data_step.id)
                    # create directory of generic_data step
                    generic_data_step_name = "STEP_" + generic_data_step.numeration + "_" + generic_data_step.type.upper()
                    path_generic_data_directory = path.join(directory_experimental_protocol, generic_data_step_name)
                    if not path.exists(path_generic_data_directory):
                        error_msg, path_generic_data_directory = create_directory(directory_experimental_protocol,
                                                                                  generic_data_step_name)
                        if error_msg != "":
                            return error_msg

                    export_generic_data_directory = path.join(export_directory_experimental_protocol,
                                                              generic_data_step_name)
                    # additional files
                    self.export_experimental_protocol_additional_files(generic_data_step, path_generic_data_directory,
                                                                       export_generic_data_directory)

            # Export data per Participant
            participant_list = Participant.objects.filter(group=group)
            if participant_list:
                # save personal data
                participant_data_list = self.process_participant_data(
                    participant_list
                )
                export_participant_filename = "%s.csv" % "Participants"
                # /EXPERIMENT_DOWNLOAD/Group_xxx/Participants.csv
                complete_participant_filename = path.join(
                    group_directory, export_participant_filename
                )
                # save personal_data_list to csv file
                save_to_csv(
                    complete_participant_filename, participant_data_list
                )
                self.files_to_zip_list.append(
                    [complete_participant_filename, export_directory_group]
                )

        return error_msg

    def export_experimental_protocol_additional_files(self, step_object, directory_step, export_directory_step):
        additional_files_list = step_object.step_additional_files.all()
        directory_additional_files = path.join(directory_step, "Additional_files")
        if len(additional_files_list) > 0 and not path.exists(directory_additional_files):
            error_msg, directory_additional_files = create_directory(directory_step, "Additional_files")
            if error_msg != "":
                return error_msg

            export_directory_additional_files = path.join(export_directory_step, "Additional_files")

        for additional_file in additional_files_list:
            file_name = additional_file.file.name
            complete_additional_filename = path.join(directory_additional_files, file_name.split('/')[-1])
            read_additional_filename = path.join(settings.MEDIA_ROOT, file_name)

            with open(read_additional_filename, "rb") as f:
                data = f.read()
            with open(complete_additional_filename, "wb") as f:
                f.write(data)

            self.files_to_zip_list.append([complete_additional_filename, export_directory_additional_files])

    def handle_exported_field(self, field):
        if field is None:
            result = ''
        elif isinstance(field, bool):
            result = _('Yes') if field else _('No')
        elif isinstance(field, Decimal):
            result = field
        else:
            result = smart_str(field)
        return result

    def get_headers_and_fields(self, output_list):
        """
            :param output_list: list with fields and headers
            :return: list of headers
                     list of fields
            """

        headers = []
        fields = []

        for element in output_list:
            if element["field"]:
                headers.append(element["header"])
                fields.append(element["field"])

        return headers, fields

    def process_participant_data(self, participants_list):
        patient_fields = [
            {"field": 'code', "header": 'participant_code',
             "description": _("Participant code")},
            {"field": 'age', "header": 'age_(years)', "description": _("Age")},
            {"field": 'gender_id', "header": 'gender',
             "description": _("Gender")},
        ]
        headers, fields = self.get_headers_and_fields(patient_fields)
        model_to_export = getattr(modules['experiments.models'], 'Participant')
        db_data = model_to_export.objects.filter(
            id__in=participants_list
        ).values_list(*fields).extra(order_by=['id'])
        export_rows_participants = [headers]

        # transform data
        for record in db_data:
            export_rows_participants.append(
                [self.handle_exported_field(field) for field in record]
            )

        # remove age data if all of them is empty
        ages_null = 0
        for row in export_rows_participants[1:]:
            if row[1] == '':
                ages_null += 1
        if ages_null == len(export_rows_participants[1:]):
            for i in range(len(export_rows_participants)):
                del export_rows_participants[i][1]

        return export_rows_participants

    def process_group_inclusion_disease(self, inclusion_criteria_list):
        export_rows_classification_of_disease = []
        if inclusion_criteria_list:
            headers, fields = self.get_headers_and_fields(classification_of_disease_fields)
            export_rows_classification_of_disease = [headers]
            for inclusion_criteria in inclusion_criteria_list:
                field_list = [inclusion_criteria.code, inclusion_criteria.description,
                              inclusion_criteria.abbreviated_description]
                export_rows_classification_of_disease.append(field_list)

        return export_rows_classification_of_disease

    def include_data_from_group(self, experiment_id):
        error_msg = ""
        experiment = get_object_or_404(Experiment, pk=experiment_id)
        group_list = Group.objects.filter(experiment=experiment)
        for group in group_list:
            group_id = group.id
            if group.id not in self.per_group_data:
                self.per_group_data[group_id] = {}
            self.per_group_data[group_id]['group'] = {
                'title': group.title,
                'description': group.description,
                'directory': '',
                'export_directory': '',
                'eeg_default_setting_id': '',
                'emg_default_setting_id': '',
                'tms_default_setting_id': '',
                'context_tree_default_id': ''
            }
            group_name_directory = "Group_" + slugify(group.title)
            group_directory = path.join(self.get_export_directory(), group_name_directory)
            export_group_directory = path.join(self.get_input_data("base_directory"), group_name_directory)
            self.per_group_data[group_id]['group']['directory'] = group_directory
            self.per_group_data[group_id]['group']['export_directory'] = export_group_directory

            self.per_group_data[group_id]['data_per_participant'] = {}
            self.per_group_data[group_id]['questionnaires_per_group'] = {}

            participant_group_list = Participant.objects.filter(group=group)
            self.per_group_data[group_id]['participant_list'] = []
            for participant in participant_group_list:
                self.per_group_data[group_id]['participant_list'].append(participant)
            participant_directory = path.join(self.per_group_data[group_id]['group']['directory'], "Participants_data")
            export_participant_directory = path.join(self.per_group_data[group_id]['group']['export_directory'],
                                                     self.input_data['participant_data_directory'])

            # questionnaire data
            step_list = Step.objects.filter(group=group, type='questionnaire')
            if step_list:
                if 'questionnaire_metadata' not in self.per_group_data[group_id]:
                    self.per_group_data[group_id]['questionnaire_metadata'] = {}
                if 'questionnaire_data' not in self.per_group_data[group_id]:
                    self.per_group_data[group_id]['questionnaire_data'] = {}
            for step_questionnaire in step_list:
                questionnaire_list = QuestionnaireResponse.objects.filter(step_id=step_questionnaire.id)
                for questionnaire in questionnaire_list:
                    participant_code = questionnaire.participant.code
                    # questionnaire response fields list
                    questionnaire_response_fields = json.loads(questionnaire.limesurvey_response)
                    questionnaire_response_list = questionnaire_response_fields['answers']
                    # add participant data to the questionnaire fields data
                    participant_data_list = self.process_participant_data([questionnaire.participant.id])
                    questionnaire_response_fields_list = participant_data_list[1]
                    questionnaire_response_fields_list.extend(questionnaire_response_list)
                    survey = get_object_or_404(
                        Questionnaire, pk=step_questionnaire.id
                    )
                    questionnaire_code = survey.code
                    # questionnaire title
                    questionnaire_default_language = \
                        get_object_or_404(
                            QuestionnaireDefaultLanguage,
                            questionnaire_id=step_questionnaire.id
                        )
                    questionnaire_title = "%s_%s" % \
                        (str(questionnaire_code),
                         slugify(
                             questionnaire_default_language.questionnaire_language.survey_name)
                         )

                    # questionnaire language
                    questionnaire_language_list = \
                        QuestionnaireLanguage.objects.filter(
                            questionnaire_id=step_questionnaire.id
                        )

                    # questionnaire_title in english
                    for questionnaire_language in questionnaire_language_list:
                        language_code = questionnaire_language.language_code
                        if language_code == 'en':
                            questionnaire_title = \
                                "%s_%s" % \
                                (str(questionnaire_code),
                                 slugify(questionnaire_language.survey_name))

                    # data per questionnaire_response
                    if questionnaire_code not in \
                            self.per_group_data[group_id]['questionnaire_data']:
                        questionnaire_header_response_list = \
                            questionnaire_response_fields['questions']
                        questionnaire_header_fields_list = \
                            participant_data_list[0]
                        questionnaire_header_fields_list.extend(
                            questionnaire_header_response_list
                        )
                        self.per_group_data[group_id]['questionnaire_data'][
                            questionnaire_code
                        ] = {
                            'questionnaire_title': questionnaire_title,
                            'questionnaire_filename':
                                "%s_%s.csv" %
                                ("Responses", str(questionnaire_code)),
                            'header': questionnaire_header_fields_list,
                            'response_list': []
                        }

                    self.per_group_data[group_id]['questionnaire_data'][
                        questionnaire_code
                    ]['response_list'].append(
                        questionnaire_response_fields_list)

                    # questionnaire data per participant
                    directory_step_name = \
                        "STEP_" + str(step_questionnaire.numeration) + "_" + \
                        step_questionnaire.type.upper()

                    participant_code_directory_name = \
                        "Participant_" + questionnaire.participant.code
                    participant_code_directory = \
                        path.join(
                            participant_directory,
                            participant_code_directory_name
                        )
                    export_participant_code_directory = \
                        path.join(
                            export_participant_directory,
                            participant_code_directory_name
                        )

                    if participant_code not in \
                            self.per_group_data[group_id][
                                'data_per_participant'
                            ]:
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code
                        ] = {}
                    if 'questionnaire_data' not in \
                            self.per_group_data[group_id][
                                'data_per_participant'
                            ][participant_code]:
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code
                        ]['questionnaire_data'] = []

                    self.per_group_data[group_id]['data_per_participant'][
                        participant_code
                    ]['questionnaire_data'].append({
                            'step_identification':
                            step_questionnaire.identification,
                            'questionnaire_response_list':
                            [questionnaire_header_fields_list,
                             questionnaire_response_fields_list],
                            'questionnaire_filename':
                            "%s.csv" % questionnaire_title,
                            'directory_step_name': directory_step_name,
                            'directory_step': path.join(
                                    participant_code_directory,
                                    directory_step_name
                                ),
                            'export_directory_step': path.join(
                                    export_participant_code_directory,
                                    directory_step_name
                                ),
                        })

                    # fill questionnaire metadata per questionnaire
                    if questionnaire_code not in \
                            self.per_group_data[group_id][
                                'questionnaire_metadata'
                            ]:
                        self.per_group_data[group_id][
                            'questionnaire_metadata'
                        ][questionnaire_code] = {}
                        questionnaire_language_list = \
                            QuestionnaireLanguage.objects.filter(
                                questionnaire_id=step_questionnaire.id
                            )
                        for questionnaire_language in \
                                questionnaire_language_list:
                            survey_metadata = \
                                questionnaire_language.survey_metadata
                            language_code = \
                                questionnaire_language.language_code

                            if language_code not in \
                                    self.per_group_data[group_id][
                                    'questionnaire_metadata'
                                    ][questionnaire_code]:
                                    self.per_group_data[group_id][
                                        'questionnaire_metadata'
                                    ][questionnaire_code][language_code] = {
                                        'metadata_fields': survey_metadata,
                                        'filename': "%s_%s_%s.csv" % ("Fields", str(questionnaire_code), language_code),
                                        'directory_name': questionnaire_title,
                                    }

            # participant with data collection
            eeg_participant_list = EEGData.objects.filter(participant__in=participant_group_list)
            for eeg_participant in eeg_participant_list:
                participant_code = eeg_participant.participant.code
                directory_step_name = "STEP_" + str(eeg_participant.step.numeration) + "_" + \
                                      eeg_participant.step.type.upper()
                participant_code_directory_name = "Participant_" + participant_code
                participant_code_directory = path.join(participant_directory, participant_code_directory_name)
                export_participant_code_directory = path.join(export_participant_directory,
                                                              participant_code_directory_name)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'eeg_data_list' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['eeg_data_list'] = []
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] = 1
                else:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] += 1
                index = str(self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'])
                self.per_group_data[group_id]['data_per_participant'][participant_code]['eeg_data_list'].append({
                    'step_identification': eeg_participant.step.identification,
                    'setting_id': eeg_participant.eeg_setting_id,
                    'data_id': eeg_participant.id,
                    'directory_step_name': directory_step_name,
                    'eeg_data_directory_name': "EEGData_" + index,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            emg_participant_list = EMGData.objects.filter(participant__in=participant_group_list)
            for emg_participant in emg_participant_list:
                participant_code = emg_participant.participant.code
                participant_code_directory_name = "Participant_" + participant_code
                directory_step_name = "STEP_" + str(emg_participant.step.numeration) + "_" + \
                                      emg_participant.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code_directory_name)
                export_participant_code_directory = path.join(export_participant_directory,
                                                              participant_code_directory_name)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'emg_data_list' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['emg_data_list'] = []
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] = 1
                else:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] += 1
                index = str(self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'])
                self.per_group_data[group_id]['data_per_participant'][participant_code]['emg_data_list'].append({
                    'step_identification': emg_participant.step.identification,
                    'setting_id': emg_participant.emg_setting_id,
                    'data_id': emg_participant.id,
                    'directory_step_name': directory_step_name,
                    'emg_data_directory_name': "EMGData_" + index,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            tms_participant_list = TMSData.objects.filter(participant__in=participant_group_list)
            for tms_participant in tms_participant_list:
                participant_code = tms_participant.participant.code
                participant_code_directory_name = "Participant_" + participant_code
                directory_step_name = "STEP_" + str(tms_participant.step.numeration) + "_" + \
                                      tms_participant.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code_directory_name)
                export_participant_code_directory = path.join(export_participant_directory,
                                                              participant_code_directory_name)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'tms_data' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['tms_data'] = []
                self.per_group_data[group_id]['data_per_participant'][participant_code]['tms_data'].append({
                    'step_identification': tms_participant.step.identification,
                    'setting_id': tms_participant.tms_setting_id,
                    'data_id': tms_participant.id,
                    'directory_step_name': directory_step_name,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            additional_data_list = AdditionalData.objects.filter(
                participant__in=participant_group_list
            )
            whole_additional_data = 0
            for additional_data in additional_data_list:
                participant_code = additional_data.participant.code
                participant_code_directory_name = \
                    "Participant_" + participant_code
                if additional_data.step:
                    directory_step_name = \
                        "STEP_" + str(additional_data.step.numeration) + \
                        "_" + additional_data.step.type.upper()
                else:
                    whole_additional_data += 1
                    directory_step_name = 'Step_0'
                participant_code_directory = path.join(
                    participant_directory, participant_code_directory_name
                )
                export_participant_code_directory = \
                    path.join(
                        export_participant_directory,
                        participant_code_directory_name
                    )
                if participant_code not in self.per_group_data[group_id][
                    'data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][
                        participant_code] = {}
                if 'additional_data_list' not in self.per_group_data[group_id][
                    'data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][
                        participant_code]['additional_data_list'] = []
                if additional_data.step:
                    if additional_data.step.type not in \
                            self.per_group_data[group_id][
                                'data_per_participant'][participant_code]:
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code][
                            additional_data.step.type] = {'data_index': 1}
                    else:
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code][
                            additional_data.step.type]['data_index'] += 1
                else:
                    if 'whole' not in \
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code]:
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code]['whole'] = {'data_index': 1}
                    else:
                        self.per_group_data[group_id]['data_per_participant'][
                            participant_code]['whole']['data_index'] += 1
                if additional_data.step:
                    index = str(self.per_group_data[group_id][
                                    'data_per_participant'][participant_code][
                                    additional_data.step.type]['data_index'])
                else:
                    index = str(self.per_group_data[group_id][
                                    'data_per_participant'][participant_code][
                                    'whole']['data_index'])
                self.per_group_data[group_id]['data_per_participant'][
                    participant_code]['additional_data_list'].append(
                    {
                        'step_identification':
                            additional_data.step.identification if
                            additional_data.step else 'Step_0',
                        'setting_id': '',
                        'data_id': additional_data.id,
                        'directory_step_name': directory_step_name,
                        'additional_data_directory_name':
                            "AdditionalData_" + index,
                        'directory_step': path.join(
                            participant_code_directory, directory_step_name
                        ),
                        'export_directory_step': path.join(
                            export_participant_code_directory,
                            directory_step_name
                        ),
                    }
                )

            generic_data_list = GenericDataCollectionData.objects.filter(
                participant__in=participant_group_list
            )
            for generic_data in generic_data_list:
                participant_code = generic_data.participant.code
                participant_code_directory_name = "Participant_" + participant_code
                directory_step_name = "STEP_" + str(generic_data.step.numeration) + "_" + \
                                      generic_data.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code_directory_name)
                export_participant_code_directory = path.join(export_participant_directory,
                                                              participant_code_directory_name)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'generic_data_list' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['generic_data_list'] = []
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] = 1
                else:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] += 1
                index = str(self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'])
                self.per_group_data[group_id]['data_per_participant'][participant_code]['generic_data_list'].append({
                    'step_identification': generic_data.step.identification,
                    'setting_id': '',
                    'data_id': generic_data.id,
                    'directory_step_name': directory_step_name,
                    'generic_data_directory_name': "GenericData_" + index,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            goalkeeper_data_list = GoalkeeperGameData.objects.filter(participant__in=participant_group_list)
            for goalkeeper_data in goalkeeper_data_list:
                participant_code = goalkeeper_data.participant.code
                participant_code_directory_name = "Participant_" + goalkeeper_data.participant.code
                directory_step_name = "STEP_" + str(goalkeeper_data.step.numeration) + "_" + \
                                      goalkeeper_data.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code_directory_name)
                export_participant_code_directory = path.join(export_participant_directory,
                                                              participant_code_directory_name)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'goalkeeper_data_list' not in self.per_group_data[group_id]['data_per_participant'][
                    participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code][
                        'goalkeeper_data_list'] = []
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] = 1
                else:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'] += 1
                index = str(self.per_group_data[group_id]['data_per_participant'][participant_code]['data_index'])
                self.per_group_data[group_id]['data_per_participant'][participant_code][
                    'goalkeeper_data_list'].append({
                        'step_identification': goalkeeper_data.step.identification,
                        'setting_id': '',
                        'data_id': goalkeeper_data.id,
                        'directory_step_name': directory_step_name,
                        'goalkeeper_data_directory_name': "GoalkeeperData_" + index,
                        'directory_step': path.join(participant_code_directory, directory_step_name),
                        'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                    })

                # stimulus_data_list = Step.objects.filter(type='stimulus')

        return error_msg

    def download_data_per_participant(self):
        error_msg = ""
        per_participant_data = self.input_data['participant_data_directory']
        for group_id in self.per_group_data:
            if self.per_group_data[group_id]['data_per_participant']:
                group_directory = self.per_group_data[group_id]['group']['directory']

                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Per_participant_data
                error_msg, group_participants_directory = create_directory(group_directory, per_participant_data)
                if error_msg != "":
                    return error_msg

                for participant_code in self.per_group_data[group_id]['data_per_participant']:
                    participant_code_directory_name = "Participant_" + participant_code
                    # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXXX
                    participant_directory = path.join(group_participants_directory, participant_code_directory_name)
                    if not path.exists(participant_directory):
                        error_msg, participant_directory = create_directory(group_participants_directory,
                                                                            participant_code_directory_name)
                        if error_msg != "":
                            return error_msg

                    # data from questionnaire
                    if 'questionnaire_data' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        questionnaire_list = self.per_group_data[group_id]['data_per_participant'][participant_code][
                            'questionnaire_data']
                        for questionnaire_data in questionnaire_list:
                            questionnaire_directory = questionnaire_data['directory_step']
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX
                            # /Step_XX_Questionnaire
                            if not path.exists(questionnaire_directory):
                                error_msg, questionnaire_directory = create_directory(participant_directory,
                                                                                      questionnaire_data[
                                                                                          'directory_step_name'])
                                if error_msg != "":
                                    return error_msg

                            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_Questionnaire
                            export_questionnaire_directory = questionnaire_data['export_directory_step']
                            filename_questionnaire = questionnaire_data['questionnaire_filename']
                            complete_filename_questionnaire = path.join(questionnaire_directory, filename_questionnaire)

                            questionnaire_description_fields = questionnaire_data['questionnaire_response_list']

                            save_to_csv(complete_filename_questionnaire, questionnaire_description_fields)

                            self.files_to_zip_list.append([complete_filename_questionnaire,
                                                           export_questionnaire_directory])

                    if 'eeg_data_list' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        eeg_data_list = self.per_group_data[group_id]['data_per_participant'][participant_code][
                            'eeg_data_list']
                        for eeg_data in eeg_data_list:
                            eeg_directory = eeg_data['directory_step']
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EEG
                            if not path.exists(eeg_directory):
                                error_msg, eeg_directory = create_directory(participant_directory,
                                                                            eeg_data['directory_step_name'])
                                if error_msg != "":
                                    return error_msg
                            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EEG
                            export_eeg_directory = eeg_data['export_directory_step']

                            # to create EEGData directory
                            directory_data_name = eeg_data['eeg_data_directory_name']
                            path_per_eeg_data = path.join(eeg_directory, directory_data_name)
                            if not path.exists(path_per_eeg_data):
                                # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123
                                # /Step_X_aaa/EEGData_index
                                error_msg, path_per_eeg_data = create_directory(eeg_directory, directory_data_name)
                                if error_msg != "":
                                    return error_msg
                            # ex. /NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123/Step_X_aaa
                            # /EEGData_index
                            export_eeg_data_directory = path.join(export_eeg_directory, directory_data_name)

                            eeg_data = get_object_or_404(EEGData, pk=eeg_data['data_id'])

                            for file in eeg_data.files.all():

                                # download eeg raw data file
                                eeg_data_filename = file.file.name.split('/')[-1]
                                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EEG
                                # /EEGData_index/eeg.raw
                                complete_eeg_data_filename = path.join(path_per_eeg_data, eeg_data_filename)
                                eeg_raw_data_file = path.join(path.join(settings.BASE_DIR, "media/"),
                                                              file.file.name)

                                with open(eeg_raw_data_file, 'rb') as f:
                                    data = f.read()

                                with open(complete_eeg_data_filename, 'wb') as f:
                                    f.write(data)

                                self.files_to_zip_list.append([complete_eeg_data_filename, export_eeg_data_directory])

                                # create eeg_setting_description
                                eeg_setting_description = get_eeg_setting_description(eeg_data.eeg_setting_id)
                                if eeg_setting_description:
                                    eeg_setting_filename = "%s_%s.json" % (eeg_data_filename.split(".")[0],
                                                                           "setting_description")

                                    # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EEG/
                                    # eeg_rawfilename_setting_description.json#
                                    complete_setting_filename = path.join(path_per_eeg_data, eeg_setting_filename)

                                    self.files_to_zip_list.append([complete_setting_filename, export_eeg_data_directory])

                                    with open(complete_setting_filename.encode('utf-8'), 'w', newline='',
                                              encoding='UTF-8') as outfile:
                                        json.dump(eeg_setting_description, outfile, indent=4)

                            # if sensor position image exist
                            if hasattr(eeg_data.eeg_setting, "eeg_electrode_localization_system"):
                                eeg_electrode_localization_system = eeg_data.eeg_setting.eeg_electrode_localization_system
                                if hasattr(eeg_electrode_localization_system, 'map_image_file'):
                                    sensor_position_filename = "%s.png" % "sensor_position"
                                    map_filename = eeg_electrode_localization_system.map_image_file.name
                                    sensors_positions_image = settings.BASE_DIR + settings.MEDIA_URL + map_filename

                                    complete_sensor_position_filename = path.join(path_per_eeg_data,
                                                                                  sensor_position_filename)

                                    with open(sensors_positions_image, 'rb') as f:
                                        data = f.read()

                                    with open(complete_sensor_position_filename, 'wb') as f:
                                        f.write(data)

                                    self.files_to_zip_list.append([complete_sensor_position_filename,
                                                                   export_eeg_data_directory])

                    if 'emg_data_list' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        emg_data_list = self.per_group_data[group_id]['data_per_participant'][participant_code][
                            'emg_data_list']
                        for emg_data in emg_data_list:
                            emg_directory = emg_data['directory_step']
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EMG
                            if not path.exists(emg_directory):
                                error_msg, emg_directory = create_directory(participant_directory,
                                                                            emg_data['directory_step_name'])
                                if error_msg != "":
                                    return error_msg
                            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EMG
                            export_emg_directory = emg_data['export_directory_step']

                            # to create EMGData directory
                            directory_data_name = emg_data['emg_data_directory_name']
                            path_per_emg_data = path.join(emg_directory, directory_data_name)
                            if not path.exists(path_per_emg_data):
                                # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123
                                # /Step_X_aaa/EMGData_index
                                error_msg, path_per_emg_data = create_directory(emg_directory, directory_data_name)
                                if error_msg != "":
                                    return error_msg
                            # ex. /NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123/Step_X_aaa
                            # /EMGData_index
                            export_emg_data_directory = path.join(export_emg_directory, directory_data_name)

                            emg_data = get_object_or_404(EMGData, pk=emg_data['data_id'])

                            for file in emg_data.files.all():

                                # download emg raw data file
                                emg_data_filename = file.file.name.split('/')[-1]
                                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EMG
                                # /EMGData_index/emg.raw
                                complete_emg_data_filename = path.join(path_per_emg_data, emg_data_filename)
                                emg_raw_data_file = path.join(path.join(settings.BASE_DIR, "media/"),
                                                              file.file.name)

                                with open(emg_raw_data_file, 'rb') as f:
                                    data = f.read()

                                with open(complete_emg_data_filename, 'wb') as f:
                                    f.write(data)

                                self.files_to_zip_list.append([complete_emg_data_filename, export_emg_data_directory])

                                # download emg_setting_description
                                emg_setting_description = get_emg_setting_description(emg_data.emg_setting_id)
                                if emg_setting_description:
                                    emg_setting_filename = "%s_%s.json" % (emg_data_filename.split(".")[0],
                                                                           "setting_description")

                                    # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EMG
                                    # /EMGData_index/emg_rawfilename_setting_description.json#
                                    complete_setting_filename = path.join(path_per_emg_data, emg_setting_filename)

                                    self.files_to_zip_list.append([complete_setting_filename, export_emg_data_directory])

                                    with open(complete_setting_filename.encode('utf-8'), 'w', newline='',
                                              encoding='UTF-8') as outfile:
                                        json.dump(emg_setting_description, outfile, indent=4)

                    if 'tms_data' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        tms_data_list = self.per_group_data[group_id]['data_per_participant'][participant_code][
                            'tms_data']
                        for tms_data in tms_data_list:
                            tms_directory = tms_data['directory_step']
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_TMS
                            if not path.exists(tms_directory):
                                error_msg, tms_directory = create_directory(participant_directory,
                                                                            tms_data['directory_step_name'])
                                if error_msg != "":
                                    return error_msg
                            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_TMS
                            export_tms_directory = tms_data['export_directory_step']

                            tms_data_description = get_tms_data_description(tms_data['data_id'])
                            if tms_data_description:
                                tms_data_filename = "%s.json" % "tms_data_description"
                                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_TMS
                                # /tms_data_description.json
                                complete_data_filename = path.join(tms_directory, tms_data_filename)

                                self.files_to_zip_list.append([complete_data_filename, export_tms_directory])

                                with open(complete_data_filename.encode('utf-8'), 'w', newline='', encoding='UTF-8') as \
                                        outfile:
                                    json.dump(tms_data_description, outfile, indent=4)

                            # TMS hotspot position image file
                            tms_data = get_object_or_404(TMSData, pk=tms_data['data_id'])

                            if tms_data.localization_system_image:
                                hotspot_image = tms_data.hot_spot_map.name
                                if hotspot_image:
                                    hotspot_map_filename = hotspot_image.split("/")[-1]
                                    # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_TMS
                                    # /hotspot_image.png
                                    complete_hotspot_filename = path.join(tms_directory, hotspot_map_filename)
                                    path_hot_spot_image = path.join(settings.BASE_DIR, "media") + "/" + hotspot_image
                                    with open(path_hot_spot_image, 'rb') as f:
                                        data = f.read()

                                    with open(complete_hotspot_filename, 'wb') as f:
                                        f.write(data)

                                    self.files_to_zip_list.append([complete_hotspot_filename, export_tms_directory])

                    if 'additional_data_list' in self.per_group_data[group_id]['data_per_participant'][
                        participant_code]:
                        additional_data_list = self.per_group_data[group_id]['data_per_participant'][
                            participant_code]['additional_data_list']
                        for additional_data in additional_data_list:
                            additional_data_directory = additional_data['directory_step']
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_step_TYPE
                            if not path.exists(additional_data_directory):
                                error_msg, additional_data_directory = create_directory(
                                    participant_directory, additional_data['directory_step_name'])
                                if error_msg != "":
                                    return error_msg
                            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_step_TYPE
                            export_data_directory = additional_data['export_directory_step']

                            # to create AdditionalData directory
                            directory_data_name = additional_data['additional_data_directory_name']
                            path_per_additional_data = path.join(additional_data_directory, directory_data_name)
                            if not path.exists(path_per_additional_data):
                                # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123
                                # /Step_X_aaa/AdditionalData_index
                                error_msg, path_per_additional_data = create_directory(additional_data_directory,
                                                                                       directory_data_name)
                                if error_msg != "":
                                    return error_msg
                            # ex. /NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123/Step_X_aaa
                            # /AdditionalData_index
                            export_additional_data_directory = path.join(export_data_directory, directory_data_name)

                            data_file = get_object_or_404(AdditionalData, pk=additional_data['data_id'])

                            for file in data_file.files.all():

                                file_name = file.file.name.split('/')[-1]
                                # read file from repository
                                additional_data_filename = path.join(settings.BASE_DIR, 'media') + '/' + \
                                                           file.file.name

                                # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Participants/PXXXX/
                                # Step_XX_step_TYPE/file_name.format_type
                                complete_additional_data_filename = path.join(path_per_additional_data, file_name)
                                with open(additional_data_filename, 'rb') as f:
                                    data = f.read()

                                with open(complete_additional_data_filename, 'wb') as f:
                                    f.write(data)

                                self.files_to_zip_list.append([complete_additional_data_filename,
                                                               export_additional_data_directory])

                    if 'goalkeeper_data_list' in self.per_group_data[group_id]['data_per_participant'][
                            participant_code]:
                        goalkeeper_data_list = self.per_group_data[group_id]['data_per_participant'][
                            participant_code]['goalkeeper_data_list']

                        for goalkeeper_data in goalkeeper_data_list:
                            goalkeeper_game_directory = goalkeeper_data['directory_step_name']
                            if not path.exists(goalkeeper_game_directory):
                                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX
                                # /Step_XX_step_TYPE
                                error_msg, goalkeeper_step_directory = create_directory(participant_directory,
                                                                                        goalkeeper_data[
                                                                                            'directory_step_name'])
                                if error_msg != "":
                                    return error_msg

                                # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_step_TYPE
                                export_data_directory = goalkeeper_data['export_directory_step']

                                # to create GoalkeeperData directory
                                directory_data_name = goalkeeper_data['goalkeeper_data_directory_name']
                                path_per_goalkeeper_data = path.join(goalkeeper_step_directory, directory_data_name)
                                if not path.exists(path_per_goalkeeper_data):
                                    # /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123
                                    # /Step_X_aaa/GoalkeeperData_index
                                    error_msg, path_per_goalkeeper_data = create_directory(goalkeeper_step_directory,
                                                                                           directory_data_name)
                                    if error_msg != "":
                                        return error_msg
                                # ex. /NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123/Step_X_aaa
                                # /GoalkeeperData_index
                                export_goalkeeper_data_directory = path.join(export_data_directory, directory_data_name)
                                # GoalkeeperGameData query
                                data_file = get_object_or_404(GoalkeeperGameData, pk=goalkeeper_data['data_id'])

                                for context_tree_file in data_file.files.all():
                                    file_name = context_tree_file.file.name.split('/')[-1]
                                    # read file from repository
                                    context_tree_filename = path.join(settings.BASE_DIR, 'media') + '/' + \
                                                            context_tree_file.file.name

                                    # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Participants/PXXXX/
                                    # Step_XX_step_TYPE/GoalkeeperData_index/file_name.format_type
                                    complete_context_tree_filename = path.join(path_per_goalkeeper_data, file_name)
                                    with open(context_tree_filename, 'rb') as f:
                                        data = f.read()

                                    with open(complete_context_tree_filename, 'wb') as f:
                                        f.write(data)

                                    self.files_to_zip_list.append([complete_context_tree_filename,
                                                                   export_goalkeeper_data_directory])

                    if 'generic_data_list' in self.per_group_data[group_id]['data_per_participant'][
                        participant_code]:
                        generic_data_list = self.per_group_data[group_id]['data_per_participant'][
                            participant_code]['generic_data_list']

                        for generic_data in generic_data_list:
                            generic_data_directory = generic_data['directory_step_name']
                            if not path.exists(generic_data_directory):
                                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX
                                # /Step_XX_step_TYPE
                                error_msg, generic_step_directory = create_directory(participant_directory, generic_data[
                                    'directory_step_name'])
                                if error_msg != "":
                                    return error_msg

                                # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_step_TYPE
                                export_data_directory = generic_data['export_directory_step']

                                # to create GoalkeeperData directory
                                directory_data_name = generic_data['generic_data_directory_name']
                                path_per_generic_data = path.join(generic_step_directory, directory_data_name)
                                if not path.exists(path_per_generic_data):
                                    # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123
                                    # /Step_X_aaa/GenericData_index
                                    error_msg, path_per_generic_data = create_directory(generic_step_directory,
                                                                                        directory_data_name)
                                    if error_msg != "":
                                        return error_msg
                                # ex. /NES_EXPORT/Experiment_data/Group_XXX/Per_participant/Participant_123/Step_X_aaa
                                # /GenericData_index
                                export_generic_data_directory = path.join(export_data_directory, directory_data_name)
                                # GenericData query
                                data_file = get_object_or_404(GenericDataCollectionData, pk=generic_data['data_id'])

                                for generic_file in data_file.files.all():
                                    generic_file_name = generic_file.file.name.split('/')[-1]
                                    # read file from repository
                                    path_generic_file = path.join(settings.BASE_DIR, 'media') + '/' + \
                                                        generic_file.file.name

                                    # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Participants/PXXXX/
                                    # Step_XX_step_TYPE/GenericData_index/file_name.format_type
                                    complete_generic_filename = path.join(path_per_generic_data, generic_file_name)
                                    with open(path_generic_file, 'rb') as f:
                                        data = f.read()

                                    with open(complete_generic_filename, 'wb') as f:
                                        f.write(data)

                                    self.files_to_zip_list.append([complete_generic_filename,
                                                                   export_generic_data_directory])

        return error_msg

    def download_data_per_questionnaire(self):
        error_msg = ''
        per_questionnaire_data = self.input_data['per_questionnaire_directory']
        per_questionnaire_metadata = self.input_data['questionnaire_metadata_directory']
        for group_id in self.per_group_data:
            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/
            group_directory = self.per_group_data[group_id]['group']['directory']
            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/
            export_directory_group = self.per_group_data[group_id]['group']['export_directory']
            if 'questionnaire_data' in self.per_group_data[group_id]:
                questionnaire_list = self.per_group_data[group_id]['questionnaire_data']
                # create 'Per_questionnaire' directory
                error_msg, group_questionnaire_directory = create_directory(group_directory, per_questionnaire_data)
                if error_msg != "":
                    return error_msg
                export_group_questionnaire_directory = path.join(export_directory_group, per_questionnaire_data)

                # create 'questionnaire_metadata' directory
                questionnaire_metadata_directory = path.join(group_directory, per_questionnaire_metadata)
                if not path.exists(questionnaire_metadata_directory):
                    error_msg, questionnaire_metadata_directory = create_directory(
                        group_directory, per_questionnaire_metadata)
                    if error_msg != "":
                        return error_msg
                # questionnaire metadata directory export
                export_questionnaire_metadata_directory = path.join(export_directory_group,
                                                                    per_questionnaire_metadata)

                for questionnaire_code in questionnaire_list:
                    questionnaire_description_fields = questionnaire_list[questionnaire_code]['response_list']
                    questionnaire_description_fields.insert(0, questionnaire_list[questionnaire_code]['header'])
                    questionnaire_title = questionnaire_list[questionnaire_code]['questionnaire_title']
                    # create questionnaire_title directory
                    error_msg, questionnaire_directory = create_directory(group_questionnaire_directory,
                                                                          questionnaire_title)
                    if error_msg != "":
                        return error_msg
                    export_questionnaire_directory = path.join(export_group_questionnaire_directory,
                                                               questionnaire_title)

                    # create directory metadata by each questionnaire
                    error_msg, questionnaire_metadata_directory_name = create_directory(
                        questionnaire_metadata_directory, questionnaire_title)
                    if error_msg != "":
                        return error_msg
                    export_questionnaire_metadata_directory_name = path.join(
                        export_questionnaire_metadata_directory, questionnaire_title)

                    # fill questionnaires responses
                    questionnaire_filename = questionnaire_list[questionnaire_code]['questionnaire_filename']
                    complete_filename_questionnaire = path.join(questionnaire_directory, questionnaire_filename)

                    save_to_csv(complete_filename_questionnaire, questionnaire_description_fields)

                    self.files_to_zip_list.append([complete_filename_questionnaire, export_questionnaire_directory])

                    # to build questionnaire metadata directory
                    if 'questionnaire_metadata' in self.per_group_data[group_id]:
                        questionnaire_metadata_list = self.per_group_data[group_id]['questionnaire_metadata'][
                            questionnaire_code]

                        for questionnaire_language in questionnaire_metadata_list:
                            questionnaire_metadata_fields = questionnaire_metadata_list[questionnaire_language][
                                'metadata_fields']
                            filename_questionnaire_metadata = questionnaire_metadata_list[questionnaire_language][
                                'filename']
                            complete_filename_questionnaire_metadata = path.join(
                                questionnaire_metadata_directory_name, filename_questionnaire_metadata)

                            with open(complete_filename_questionnaire_metadata, 'w') as f:
                                f.write(questionnaire_metadata_fields)

                            self.files_to_zip_list.append([complete_filename_questionnaire_metadata,
                                                           export_questionnaire_metadata_directory_name])

        return error_msg


def get_eeg_setting_description(eeg_setting_id):
    eeg_setting = get_object_or_404(EEGSetting, pk=eeg_setting_id)

    eeg_setting_attributes = vars(eeg_setting)

    eeg_setting_attributes = handling_values(eeg_setting_attributes)

    description = {
        'name': eeg_setting_attributes['name'],
        'description': eeg_setting_attributes['description'],
    }

    if hasattr(eeg_setting, 'eeg_amplifier_setting'):
        eeg_amplifier_setting_attributes = vars(eeg_setting.eeg_amplifier_setting)
        eeg_amplifier_setting_attributes = handling_values(eeg_amplifier_setting_attributes)
        eeg_amplifier_attributes = vars(eeg_setting.eeg_amplifier_setting.eeg_amplifier)
        eeg_amplifier_attributes = handling_values(eeg_amplifier_attributes)
        impedance_description = ''
        if eeg_amplifier_attributes['input_impedance'] and eeg_amplifier_attributes['input_impedance_unit']:
            impedance_description = eeg_amplifier_attributes['input_impedance'] + " (" + eeg_amplifier_attributes[
                'input_impedance_unit'] + ")"
        description['eeg_amplifier_setting'] = {
            'identification': eeg_amplifier_attributes['identification'],
            'manufacturer_name': eeg_amplifier_attributes['manufacturer_name'],
            'serial_number': eeg_amplifier_attributes['serial_number'],
            'description': eeg_amplifier_attributes['description'],
            'gain_setted': eeg_amplifier_setting_attributes['gain'],
            'sampling_rate_setted': eeg_amplifier_setting_attributes['sampling_rate'],
            'number_of_channels_used': eeg_amplifier_setting_attributes['number_of_channels_used'],
            'gain (equipment)': eeg_amplifier_attributes['gain'],
            'number_of_channels (equipment)': eeg_amplifier_attributes['number_of_channels'],
            'common_mode_rejection_ratio': eeg_amplifier_attributes['common_mode_rejection_ratio'],
            'input_impedance': impedance_description,
            'amplifier_detection_type_name': eeg_amplifier_attributes['amplifier_detection_type_name'],
            'tethering_system_name': eeg_amplifier_attributes['tethering_system_name'],
        }

    if hasattr(eeg_setting, 'eeg_filter_setting'):
        eeg_filter_setting_attributes = vars(eeg_setting.eeg_filter_setting)
        eeg_filter_setting_attributes = handling_values(eeg_filter_setting_attributes)
        description['eeg_filter_setting'] = {
            'filter_type': eeg_filter_setting_attributes['eeg_filter_type_name'],
            'description': eeg_filter_setting_attributes['eeg_filter_type_description'],
            'high_pass': eeg_filter_setting_attributes['high_pass'],
            'low_pass': eeg_filter_setting_attributes['low_pass'],
            'order': eeg_filter_setting_attributes['order'],
            'high_band_pass': eeg_filter_setting_attributes['high_band_pass'],
            'low_band_pass': eeg_filter_setting_attributes['low_band_pass'],
            'high_notch': eeg_filter_setting_attributes['high_notch'],
            'low_notch': eeg_filter_setting_attributes['low_notch']
        }

    if hasattr(eeg_setting, 'eeg_solution'):
        eeg_solution_attributes = vars(eeg_setting.eeg_solution)
        eeg_solution_attributes = handling_values(eeg_solution_attributes)
        description['eeg_solution_setting'] = {
            'manufacturer': eeg_solution_attributes['manufacturer_name'],
            'identification': eeg_solution_attributes['name'],
            'components': eeg_solution_attributes['components']
        }

    if hasattr(eeg_setting, 'eeg_electrode_net'):
        eeg_electrode_net_attributes = vars(eeg_setting.eeg_electrode_net)
        eeg_electrode_net_attributes = handling_values(eeg_electrode_net_attributes)
        description['eeg_electrode_net'] = {
            'manufacturer_name': eeg_electrode_net_attributes['manufacturer_name'],
            'equipment_type': eeg_electrode_net_attributes['equipment_type'],
            'identification': eeg_electrode_net_attributes['identification'],
            'description': eeg_electrode_net_attributes['description'],
            'serial_number': eeg_electrode_net_attributes['serial_number'],
        }

    if hasattr(eeg_setting, 'eeg_electrode_localization_system'):
        eeg_electrode_localization_system_attributes = vars(eeg_setting.eeg_electrode_localization_system)
        eeg_electrode_localization_system_attributes = handling_values(eeg_electrode_localization_system_attributes)
        description['eeg_electrode_localization_system'] = {
            'name': eeg_electrode_localization_system_attributes['name'],
            'description': eeg_electrode_localization_system_attributes['description'],
            'image_filename': eeg_electrode_localization_system_attributes['map_image_file'].split('/')[-1],
            'electrode_position_list': [],
        }

        eeg_electrode_position_list = EEGElectrodePosition.objects.filter(
            eeg_electrode_localization_system=eeg_setting.eeg_electrode_localization_system)
        for eeg_electrode_position in eeg_electrode_position_list:
            eeg_electrode_position_attributes = vars(eeg_electrode_position)
            eeg_electrode_position_attributes = handling_values(eeg_electrode_position_attributes)
            description['eeg_electrode_localization_system']['electrode_position_list'].append({
                'name': eeg_electrode_position_attributes['name'],
                'coordinate_x': eeg_electrode_position_attributes['coordinate_x'],
                'coordinate_y': eeg_electrode_position_attributes['coordinate_y'],
                'channel_index': eeg_electrode_position_attributes['channel_index'],
                'electrode_model': {}
            })

            if hasattr(eeg_electrode_position, 'electrode_model'):
                electrode_model_attributes = vars(eeg_electrode_position.electrode_model)
                electrode_model_attributes = handling_values(electrode_model_attributes)
                impedance_description = ''
                electrode_distance_description = ''
                if electrode_model_attributes['impedance'] and electrode_model_attributes['impedance_unit']:
                    impedance_description = electrode_model_attributes['impedance'] + " (" + electrode_model_attributes[
                        'impedance_unit'] + ")"
                if electrode_model_attributes['inter_electrode_distance'] and \
                        electrode_model_attributes['inter_electrode_distance_unit']:
                    electrode_distance_description = electrode_model_attributes['inter_electrode_distance'] + " (" + \
                                                     electrode_model_attributes['inter_electrode_distance_unit'] + ")"
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'model_name'] = electrode_model_attributes['name']
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'electrode type'] = electrode_model_attributes['electrode_type']
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'description'] = electrode_model_attributes['description']
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'material'] = electrode_model_attributes['material']
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'usability'] = electrode_model_attributes['usability']
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'impedance'] = impedance_description
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'distance_inter_electrode'] = electrode_distance_description
                description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                    'electrode_configuration_name'] = electrode_model_attributes['electrode_configuration_name']

                if hasattr(eeg_electrode_position.electrode_model, 'surfaceelectrode'):
                    surface_electrode_attributes = vars(eeg_electrode_position.electrode_model.surfaceelectrode)
                    surface_electrode_attributes = handling_values(surface_electrode_attributes)
                    electrode_shape_measure_description = ''
                    if surface_electrode_attributes['electrode_shape_measure_value'] and surface_electrode_attributes[
                        'electrode_shape_measure_unit']:
                        electrode_shape_measure_description = surface_electrode_attributes['electrode_shape_measure']\
                                                              + " (" + surface_electrode_attributes[
                            'electrode_shape_measure_unit'] + ")"

                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'surface_electrode'] = {}
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'surface_electrode']['conduction_type'] = surface_electrode_attributes['conduction_type']
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'surface_electrode']['electrode_mode'] = surface_electrode_attributes['electrode_mode']
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'surface_electrode']['electrode_shape_measure'] = electrode_shape_measure_description
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'surface_electrode']['electrode_shape_name'] = surface_electrode_attributes[
                        'electrode_shape_name']

                if hasattr(eeg_electrode_position.electrode_model, 'intramuscular_electrode'):
                    intramuscular_electrode_attributes = vars(
                        eeg_electrode_position.electrode_model.intramuscular_electrode)
                    intramuscular_electrode_attributes = handling_values(intramuscular_electrode_attributes)
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1][
                        'electrode_model']['intramuscular_electrode'] = {}
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1][
                        'electrode_model']['intramuscular_electrode']['strand'] = intramuscular_electrode_attributes[
                        'strand']
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1][
                        'electrode_model']['intramuscular_electrode']['insulation_material_name'] = \
                        intramuscular_electrode_attributes['insulation_material_name']
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1][
                        'electrode_model']['intramuscular_electrode']['insulation_material_description'] = \
                        intramuscular_electrode_attributes['insulation_material_description']
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1][
                        'electrode_model']['intramuscular_electrode']['lenght_of_exposed_tip'] = \
                        intramuscular_electrode_attributes['lenght_of_exposed_tip']

                if hasattr(eeg_electrode_position.electrode_model, 'needle_electrode'):
                    needle_electrode_attributes = vars(eeg_electrode_position.electrode_model.needle_electrode)
                    needle_electrode_attributes = handling_values(needle_electrode_attributes)
                    size_description = ''
                    if needle_electrode_attributes['size_of_conductive_contact_points_at_the_tip'] and \
                            needle_electrode_attributes['size_unit']:
                        size_description = surface_electrode_attributes[
                                                                  'size_of_conductive_contact_points_at_the_tip'] \
                                                              + " (" + surface_electrode_attributes['size_unit'] + ")"
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'needle_electrode'] = {}
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'needle_electrode']['size'] = needle_electrode_attributes['size']
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'needle_electrode']['size_of_conductive_contact_points_at_the_tip'] = size_description
                    description['eeg_electrode_localization_system']['electrode_position_list'][-1]['electrode_model'][
                        'needle_electrode']['number_of_conductive_contact_points_at_the_tip'] = \
                        needle_electrode_attributes['number_of_conductive_contact_points_at_the_tip']

    return description


def handling_values(dictionary_object):
    result = {}
    for key, value in dictionary_object.items():
        if dictionary_object[key] is None:
            result[key] = ''
        elif isinstance(dictionary_object[key], bool):
            result[key] = _('Yes') if dictionary_object[key] else _('No')
        else:
            result[key] = smart_str(dictionary_object[key])

    return result


def get_emg_setting_description(emg_setting_id):
    emg_setting = get_object_or_404(EMGSetting, pk=emg_setting_id)

    emg_setting_attributes = vars(emg_setting)

    emg_setting_attributes = handling_values(emg_setting_attributes)

    description = {
        'name': emg_setting_attributes['name'],
        'description': emg_setting_attributes['description'],
        'acquisition_software': emg_setting_attributes['acquisition_software_version'],
    }

    if hasattr(emg_setting, 'emg_ad_converter_setting'):
        emg_ad_converter_setting_attributes = vars(emg_setting.emg_ad_converter_setting)
        emg_ad_converter_setting_attributes = handling_values(emg_ad_converter_setting_attributes)

        description['emg_ad_converter_setting'] = {
            'sampling_rate_setted': emg_ad_converter_setting_attributes['sampling_rate']
        }

        ad_converter_attributes = vars(emg_setting.emg_ad_converter_setting.ad_converter)
        ad_converter_attributes = handling_values(ad_converter_attributes)
        description['emg_ad_converter_setting']['ad_converter'] = ad_converter_attributes['identification']
        description['emg_ad_converter_setting']['sample_rate (equipment)'] = ad_converter_attributes[
            'sampling_rate']
        description['emg_ad_converter_setting']['signal_to_noise (equipment)'] = ad_converter_attributes[
            'signal_to_noise_rate']
        description['emg_ad_converter_setting']['resolution (equipment)'] = ad_converter_attributes['resolution']

    if hasattr(emg_setting, 'emg_digital_filter_setting'):
        emg_digital_filter_setting = vars(emg_setting.emg_digital_filter_setting)
        emg_digital_filter_setting = handling_values(emg_digital_filter_setting)
        description['emg_digital_filter_setting'] = {
            'filter type name': emg_digital_filter_setting['filter_type_name'],
            'description': emg_digital_filter_setting['filter_type_description'],
            'high_pass': emg_digital_filter_setting['high_pass'],
            'low_pass': emg_digital_filter_setting['low_pass'],
            'high_band_pass': emg_digital_filter_setting['high_band_pass'],
            'low_band_pass': emg_digital_filter_setting['low_band_pass'],
            'high_notch': emg_digital_filter_setting['high_notch'],
            'low_notch': emg_digital_filter_setting['low_notch'],
            'order': emg_digital_filter_setting['order'],
        }

    description['emg_electrode_setting_list'] = []

    # to_many
    emg_electrode_setting_list = EMGElectrodeSetting.objects.filter(emg_setting=emg_setting)
    for emg_electrode_setting in emg_electrode_setting_list:

        emg_electrode_setting_dict = {}

        electrode_model_attributes = vars(emg_electrode_setting.electrode_model)
        electrode_model_attributes = handling_values(electrode_model_attributes)

        impedance_description = ''
        if electrode_model_attributes['impedance'] and electrode_model_attributes['impedance_unit']:
            impedance_description = \
                electrode_model_attributes['impedance'] + " (" + electrode_model_attributes['impedance_unit'] + ")"

        electrode_distance_description = ''
        if electrode_model_attributes['inter_electrode_distance'] and \
                electrode_model_attributes['inter_electrode_distance_unit']:
            electrode_distance_description = electrode_model_attributes['inter_electrode_distance'] + " (" + \
                                             electrode_model_attributes['inter_electrode_distance_unit'] + ")"

        emg_electrode_setting_dict['electrode_model'] = {
            'model_name': electrode_model_attributes['name'],
            'electrode type': electrode_model_attributes['electrode_type'],
            'description': electrode_model_attributes['description'],
            'material': electrode_model_attributes['material'],
            'usability': electrode_model_attributes['usability'],
            'impedance': impedance_description,
            'distance inter electrode': electrode_distance_description,
            'electrode_configuration_name': electrode_model_attributes['electrode_configuration_name'],
        }

        if hasattr(emg_electrode_setting, 'emg_amplifier_setting'):
            emg_amplifier_setting_attributes = vars(emg_electrode_setting.emg_amplifier_setting)
            emg_amplifier_setting_attributes = handling_values(emg_amplifier_setting_attributes)
            emg_amplifier_attributes = vars(emg_electrode_setting.emg_amplifier_setting.amplifier)
            emg_amplifier_attributes = handling_values(emg_amplifier_attributes)
            impedance_description = emg_amplifier_attributes['input_impedance'] + " (" + emg_amplifier_attributes[
                'input_impedance_unit'] + ")"
            emg_electrode_setting_dict['emg_amplifier_setting'] = {
                'identification': emg_amplifier_attributes['identification'],
                'manufacturer_name': emg_amplifier_attributes['manufacturer_name'],
                'serial_number': emg_amplifier_attributes['serial_number'],
                'description': emg_amplifier_attributes['description'],
                'gain_setted': emg_amplifier_setting_attributes['gain'],
                'gain (equipment)': emg_amplifier_attributes['gain'],
                'number_of_channels (equipment)': emg_amplifier_attributes['number_of_channels'],
                'common_mode_rejection_ratio': emg_amplifier_attributes['common_mode_rejection_ratio'],
                'input_impedance': impedance_description,
                'amplifier_detection_type_name': emg_amplifier_attributes['amplifier_detection_type_name'],
                'tethering_system_name': emg_amplifier_attributes['tethering_system_name'],
            }

            if hasattr(emg_electrode_setting.emg_amplifier_setting, 'emg_analog_filter_setting'):
                emg_amplifier_setting = emg_electrode_setting.emg_amplifier_setting
                emg_analog_filter_setting_attributes = vars(emg_amplifier_setting.emg_analog_filter_setting)
                emg_analog_filter_setting_attributes = handling_values(emg_analog_filter_setting_attributes)

                emg_electrode_setting_dict['emg_amplifier_setting']['emg_analog_filter_setting'] = {
                    'low_pass': emg_analog_filter_setting_attributes['low_pass'],
                    'high_pass': emg_analog_filter_setting_attributes['high_pass'],
                    'low_band_pass': emg_analog_filter_setting_attributes['low_band_pass'],
                    'high_band_pass': emg_analog_filter_setting_attributes['high_band_pass'],
                    'low_notch': emg_analog_filter_setting_attributes['low_notch'],
                    'high_notch': emg_analog_filter_setting_attributes['high_notch'],
                    'order': emg_analog_filter_setting_attributes['order'],
                }

        if hasattr(emg_electrode_setting, 'emg_preamplifier_setting'):
            emg_preamplifier_setting_attributes = vars(emg_electrode_setting.emg_preamplifier_setting)
            emg_preamplifier_setting_attributes = handling_values(emg_preamplifier_setting_attributes)
            amplifier_attributes = vars(emg_electrode_setting.emg_preamplifier_setting.amplifier)
            amplifier_attributes = handling_values(amplifier_attributes)
            preamplifier_impedance_description = ''
            if amplifier_attributes['input_impedance'] and amplifier_attributes['input_impedance_unit']:
                preamplifier_impedance_description = amplifier_attributes['input_impedance'] + " (" + \
                                                     amplifier_attributes['input_impedance_unit'] + ")"

            emg_electrode_setting_dict['emg_preamplifier_setting'] = {
                'amplifier_name': amplifier_attributes['identification'],
                'manufacturer_name': amplifier_attributes['manufacturer_name'],
                'description': amplifier_attributes['description'],
                'serial_number': amplifier_attributes['serial_number'],
                'gain_setted': emg_preamplifier_setting_attributes['gain'],
                'gain (equipment)': amplifier_attributes['gain'],
                'number of channels': amplifier_attributes['number_of_channels'],
                'common_mode_rejection_ratio': amplifier_attributes['common_mode_rejection_ratio'],
                'impedance': preamplifier_impedance_description,
                'detection type': amplifier_attributes['amplifier_detection_type_name'],
                'tethering system': amplifier_attributes['tethering_system_name'],
            }

            if hasattr(emg_electrode_setting.emg_preamplifier_setting,
                       'emg_preamplifier_filter_setting'):
                emg_preamplifier_setting = emg_electrode_setting.emg_preamplifier_setting
                emg_preamplifier_filter_setting_attributes = \
                    vars(emg_preamplifier_setting.emg_preamplifier_filter_setting)
                emg_preamplifier_filter_setting_attributes = handling_values(emg_preamplifier_filter_setting_attributes)

                emg_electrode_setting_dict['emg_preamplifier_setting']['emg_preamplifier_filter_setting'] = {
                    'low_pass': emg_preamplifier_filter_setting_attributes['low_pass'],
                    'high_pass': emg_preamplifier_filter_setting_attributes['high_pass'],
                    'low_band_pass': emg_preamplifier_filter_setting_attributes['low_band_pass'],
                    'high_band_pass': emg_preamplifier_filter_setting_attributes['high_band_pass'],
                    'low_notch': emg_preamplifier_filter_setting_attributes['low_notch'],
                    'high_notch': emg_preamplifier_filter_setting_attributes['high_notch'],
                    'order': emg_preamplifier_filter_setting_attributes['order'],
                }

        if hasattr(emg_electrode_setting, 'emg_electrode_placement_setting'):
            emg_electrode_placement_setting_attributes = vars(emg_electrode_setting.emg_electrode_placement_setting)
            emg_electrode_placement_setting_attributes = handling_values(emg_electrode_placement_setting_attributes)
            emg_electrode_setting_dict['emg_electrode_placement_setting'] = {
                'muscle name': emg_electrode_placement_setting_attributes['muscle_name'],
                'muscle side': emg_electrode_placement_setting_attributes['muscle_side'],
                'remarks': emg_electrode_placement_setting_attributes['remarks'],
            }

            if hasattr(emg_electrode_setting.emg_electrode_placement_setting, 'emg_electrode_placement'):
                emg_electrode_placement_setting = emg_electrode_setting.emg_electrode_placement_setting
                emg_electrode_placement_attributes = vars(emg_electrode_placement_setting.emg_electrode_placement)
                emg_electrode_setting_dict['emg_electrode_placement_setting']['electrode_placement'] = {
                    'standardization system': emg_electrode_placement_attributes['standardization_system_name'],
                    'standardization system description': emg_electrode_placement_attributes[
                        'standardization_system_description'],
                    'muscle_anatomy_origin': emg_electrode_placement_attributes['muscle_anatomy_origin'],
                    'muscle_anatomy_insertion': emg_electrode_placement_attributes['muscle_anatomy_insertion'],
                    'muscle_anatomy_function': emg_electrode_placement_attributes['muscle_anatomy_function'],
                    'location': emg_electrode_placement_attributes['location'],
                    'placement type': emg_electrode_placement_attributes['placement_type'],
                }

                emg_electrode_placement = emg_electrode_placement_setting.emg_electrode_placement
                if emg_electrode_placement.placement_type == 'intramuscular':
                    emg_intramuscular_placement = \
                        get_object_or_404(EMGIntramuscularPlacement, pk=emg_electrode_placement.id)
                    emg_intramuscular_placement_attributes = vars(emg_intramuscular_placement)
                    emg_intramuscular_placement_attributes = handling_values(emg_intramuscular_placement_attributes)
                    emg_electrode_setting_dict['emg_electrode_placement_setting']['electrode_placement'][
                        'placement_type_description'] = {
                            'method_of_insertion': emg_intramuscular_placement_attributes['method_of_insertion'],
                            'depth_of_insertion': emg_intramuscular_placement_attributes['depth_of_insertion'],
                        }

                if emg_electrode_placement.placement_type == 'needle':
                    emg_needle_placement = get_object_or_404(EMGNeedlePlacement, pk=emg_electrode_placement.id)
                    emg_needle_placement_attributes = vars(emg_needle_placement)
                    emg_needle_placement_attributes = handling_values(emg_needle_placement_attributes)
                    emg_electrode_setting_dict['emg_electrode_placement_setting']['electrode_placement'][
                        'placement_type_description'] = {
                            'depth_of_insertion': emg_needle_placement_attributes['depth_of_insertion'],
                        }

                if emg_electrode_placement.placement_type == 'surface':
                    emg_surface_placement = get_object_or_404(EMGSurfacePlacement, pk=emg_electrode_placement.id)
                    emg_surface_placement_attributes = vars(emg_surface_placement)
                    emg_surface_placement_attributes = handling_values(emg_surface_placement_attributes)
                    emg_electrode_setting_dict['emg_electrode_placement_setting']['electrode_placement'][
                        'placement_type_description'] = {
                            'start_posture': emg_surface_placement_attributes['start_posture'],
                            'orientation': emg_surface_placement_attributes['orientation'],
                            'fixation_on_the_skin': emg_surface_placement_attributes['fixation_on_the_skin'],
                            'reference_electrode': emg_surface_placement_attributes['reference_electrode'],
                            'clinical_test': emg_surface_placement_attributes['clinical_test'],
                        }

        description['emg_electrode_setting_list'].append(emg_electrode_setting_dict)

    return description


def get_tms_data_description(tms_data_id):
    tms_description = {}
    tms_data = get_object_or_404(TMSData, pk=tms_data_id)

    tms_data_attributes = vars(tms_data)

    tms_data_attributes = handling_values(tms_data_attributes)

    tms_description['stimulation_description'] = {
        'tms_stimulation_description': tms_data_attributes['description'],
        'resting_motor threshold-RMT(%)': tms_data_attributes['resting_motor_threshold'],
        'test_pulse_intensity_of_simulation(% over the %RMT)': tms_data_attributes[
            'test_pulse_intensity_of_simulation'],
        'interval_between_pulses': tms_data_attributes['interval_between_pulses'],
        'interval_between_pulses_unit': tms_data_attributes['interval_between_pulses_unit'],
        'repetitive_pulse_frequency': tms_data_attributes['repetitive_pulse_frequency'],
        'coil_orientation': tms_data_attributes['coil_orientation'],
        'coil_orientation_angle': tms_data_attributes['coil_orientation_angle'],
        'second_test_pulse_intensity (% over the %RMT)': tms_data_attributes['second_test_pulse_intensity'],
        'time_between_mep_trials': tms_data_attributes['time_between_mep_trials'],
        'time_between_mep_trials_unit': tms_data_attributes['time_between_mep_trials_unit'],
    }

    tms_description['hotspot_position'] = {
        'hot_spot_map_filename': tms_data_attributes['hot_spot_map'].split('/')[-1],
        'tms_localization_system_name': tms_data_attributes['localization_system_name'],
        'tms_localization_system_description': tms_data_attributes['localization_system_description'],
        'brain_area': tms_data_attributes['brain_area_name'],
        'brain_area_description': tms_data_attributes['brain_area_description'],
        'brain_area_system_name': tms_data_attributes['brain_area_system_name'],
        'brain_area_system_description': tms_data_attributes['brain_area_system_description']
    }

    if hasattr(tms_data, 'tms_setting'):
        tms_setting_attributes = vars(tms_data.tms_setting)
        tms_setting_attributes = handling_values(tms_setting_attributes)

        tms_description['tms_setting'] = {
            'name': tms_setting_attributes['name'],
            'description': tms_setting_attributes['description'],
        }

    if hasattr(tms_data.tms_setting, 'tms_device_setting'):
        tms_device_setting_attributes = vars(tms_data.tms_setting.tms_device_setting)
        tms_device_setting_attributes = handling_values(tms_device_setting_attributes)

        tms_coil_model_attributes = vars(tms_data.tms_setting.tms_device_setting.coil_model)
        tms_coil_model_attributes = handling_values(tms_coil_model_attributes)

        tms_device_attributes = vars(tms_data.tms_setting.tms_device_setting.tms_device)
        tms_device_attributes = handling_values(tms_device_attributes)

        tms_description['tms_device_setting'] = {
            'pulse_stimulus_type': tms_device_setting_attributes['pulse_stimulus_type'],
            'manufacturer_name': tms_device_attributes['manufacturer_name'],
            'equipment_type': tms_device_attributes['equipment_type'],
            'identification': tms_device_attributes['identification'],
            'description': tms_device_attributes['description'],
            'serial_number': tms_device_attributes['serial_number'],
            'pulse_type': tms_device_attributes['pulse_type'],
            'coil_name': tms_coil_model_attributes['name'],
            'coil_description': tms_coil_model_attributes['description'],
            'coil_shape_name': tms_coil_model_attributes['coil_shape_name'],
            'material_name': tms_coil_model_attributes['material_name'],
            'material_description': tms_coil_model_attributes['material_description'],
            'coil_design': tms_coil_model_attributes['coil_design'],
        }

    return tms_description


def get_tms_setting_description(tms_setting_id):
    tms_setting_description = {}
    tms_setting = get_object_or_404(TMSSetting, pk=tms_setting_id)

    if tms_setting:
        tms_setting_description = {
            'name': tms_setting.name,
            'description': tms_setting.description if tms_setting.description else '',
        }

    return tms_setting_description


def get_context_tree_description(context_tree_id):
    context_tree = get_object_or_404(ContextTree, pk=context_tree_id)
    context_tree_attributes = vars(context_tree)
    context_tree_attributes = handling_values(context_tree_attributes)

    context_tree_description = {
        'name': context_tree_attributes['name'],
        'description': context_tree_attributes['description'],
        'setting_text': context_tree_attributes['setting_text'],
        'setting_filename': context_tree_attributes['setting_file'].split('/')[-1],
    }

    return context_tree_description
