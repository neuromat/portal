import json
from os import path, makedirs
from csv import writer
from django.conf import settings
from django.shortcuts import get_object_or_404

from experiments.models import Experiment, Group, Participant, EEGData, EMGData, EEGSetting, EMGSetting, TMSData, \
    TMSSetting, AdditionalData, ContextTree, GenericDataCollectionData, GoalkeeperGameData, Stimulus, Step

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


def save_to_csv(complete_filename, rows_to_be_saved):
    """
    :param complete_filename: filename and directory structure where file is going to be saved
    :param rows_to_be_saved: list of rows that are going to be written on the file
    :return:
    """
    with open(complete_filename.encode('utf-8'), 'w', newline='', encoding='UTF-8') as csv_file:
        export_writer = writer(csv_file)
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
        return ("Base path does not exist"), complete_path

    complete_path = path.join(basedir, path_to_create)

    # print("encode: ", sys.getfilesystemencoding(), sys.getdefaultencoding())
    # print("create_directory-encode:", complete_path.encode('utf-8'))
    if not path.exists(complete_path.encode('utf-8')):
        # print("create_directory:", basedir, path_to_create)
        # print("create_directory:", complete_path)
        makedirs(complete_path.encode('utf-8'))

    return "", complete_path


class ExportExecution:
    def get_username(self, request):
        self.user_name = None
        if request.user.is_authenticated():
            self.user_name = request.user.username
        return self.user_name

    def set_directory_base(self, export_id):
        self.directory_base = path.join(self.base_directory_name, str(export_id))

    def get_directory_base(self):

        return self.directory_base  # MEDIA_ROOT/download/export_id

    def __init__(self, export_id):
        # self.get_session_key()

        # questionnaire_id = 0
        self.files_to_zip_list = []
        # self.headers = []
        # self.fields = []
        self.directory_base = ''
        self.base_directory_name = path.join(settings.MEDIA_ROOT, "download")
        # self.directory_base = self.base_directory_name
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

        error_msg, self.base_export_directory = create_directory(self.get_directory_base(), base_directory)

        return error_msg

    def get_input_data(self, key):

        if key in self.input_data.keys():
            return self.input_data[key]
        return ""

    def get_export_directory(self):

        return self.base_export_directory   # MEDIA_ROOT/download/username_id/export_id/NES_EXPORT

    # Dados gerais do experimento
    def process_experiment_data(self, experiment_id):
        error_msg = ""
        experiment = get_object_or_404(Experiment, pk=experiment_id)
        # group_list = Group.objects.filter(experiment=experiment)
        # process of experiment description

        study = experiment.study
        experiment_resume_header = ['Study', 'Study description', 'Start date', 'End date', 'Experiment',
                                    'Experiment description']

        experiment_resume = [study.title, study.description, str(study.start_date), str(study.end_date),
                             experiment.title, experiment.description]

        filename_experiment_resume = "%s.csv" % "Experiment"

        # path ex. /EXPERIMENT_DOWNLOAD/
        export_experiment_data = self.get_input_data("base_directory")

        # # path ex. UserS/.../qdc/media/.../EXPERIMENT_DOWNLOAD/
        experiment_resume_directory = self.get_export_directory()
        # Users/.../qdc/media/.../EXPERIMENT_DOWNLOAD/Experiment.csv
        complete_filename_experiment_resume = path.join(experiment_resume_directory, filename_experiment_resume)

        experiment_description_fields = []
        experiment_description_fields.insert(0, experiment_resume_header)
        experiment_description_fields.insert(1, experiment_resume)
        save_to_csv(complete_filename_experiment_resume, experiment_description_fields)

        self.files_to_zip_list.append([complete_filename_experiment_resume, export_experiment_data])

        # process data for each group
        group_list = Group.objects.filter(experiment=experiment)
        for group in group_list:
            if group.experimental_protocol:
                group_resume = "Group name: " + group.title + "\n" + "Group description: " + group.description + "\n"
                group_directory_name = 'Group_' + group.title

                # group_directory = Users/.../qdc/media/.../EXPERIMENT_DOWNLOAD/Group_group.title
                error_msg, group_directory = create_directory(experiment_resume_directory, group_directory_name)
                if error_msg != "":
                    return error_msg
                # export_directory_group = EXPERIMENT_DOWNLOAD/Group_group.title
                export_directory_group = path.join(export_experiment_data, group_directory_name)

                # ex. Users/..../EXPERIMENT_DOWNLOAD/Group_xxx/Experimental_protocol
                error_msg, directory_experimental_protocol = create_directory(group_directory, "Experimental_protocol")
                if error_msg != "":
                    return error_msg

                # export_directory_experimental_protocol = EXPERIMENT_DOWNLOAD/Group_group.title/Experimental_protocol
                export_directory_experimental_protocol = path.join(export_directory_group, "Experimental_protocol")

                # save experimental protocol description
                experimental_protocol_description = group.experimental_protocol.textual_description
                if experimental_protocol_description:
                    filename_experimental_protocol = "%s.txt" % "Experimental_protocol_description"
                    # ex. Users/..../EXPERIMENT_DOWNLOAD/Group_xxx/Experimental_protocol
                    # /Experimental_protocol_description.txt
                    complete_filename_experimental_protocol = path.join(directory_experimental_protocol,
                                                                        filename_experimental_protocol)

                    self.files_to_zip_list.append([complete_filename_experimental_protocol,
                                                   export_directory_experimental_protocol])

                    with open(complete_filename_experimental_protocol.encode('utf-8'), 'w', newline='',
                              encoding='UTF-8') as txt_file:
                        txt_file.writelines(group_resume)
                        txt_file.writelines(experimental_protocol_description)

                # save protocol image
                experimental_protocol_image = group.experimental_protocol.image
                if experimental_protocol_image:
                    filename_protocol_image = "Experimental_protocol_image.png"
                    complete_protocol_image_filename = path.join(directory_experimental_protocol,
                                                                 filename_protocol_image)
                    self.files_to_zip_list.append([complete_protocol_image_filename,
                                                   export_directory_experimental_protocol])

                    image_protocol = path.join(path.join(settings.BASE_DIR,"media/"), experimental_protocol_image.name)
                    with open(image_protocol, 'rb') as f:
                        data = f.read()

                    with open(complete_protocol_image_filename, 'wb') as f:
                        f.write(data)

            # Export data per Participant
            header_personal_data = ["Participant_code", "Age", "Gender"]
            personal_data_list = []
            personal_data_list.insert(0, header_personal_data)
            participant_list = Participant.objects.filter(group=group)
            for participant in participant_list:
                # save personal data
                data = [participant.code, participant.age, participant.gender]
                personal_data_list.append(data)

                export_participant_filename = "%s.csv" % "Participants"
                # ex. ex. Users/..../EXPERIMENT_DOWNLOAD/Group_xxx/Participants.csv
                complete_participant_filename = path.join(group_directory, export_participant_filename)
                # save personal_data_list to csv file
                save_to_csv(complete_participant_filename, personal_data_list)
                self.files_to_zip_list.append([complete_participant_filename, export_directory_group])

                # save eeg, emg, tms, context tree setting data

                # save eeg, emg, tms, context tree setting default in Experimental Protocol directory
        #         if 'eeg_default_setting_id' in self.per_group_data[group_id]:
        #             eeg_default_setting_description = get_eeg_setting_description(self.per_group_data[group_id][
        #                                                                               'eeg_default_setting_id'])
        #             eeg_setting_description = "%s.json" % "eeg_default_setting"
        #             complete_filename_eeg_setting = path.join(directory_experimental_protocol, eeg_setting_description)
        #             self.files_to_zip_list.append([complete_filename_eeg_setting,
        #                                            export_directory_experimental_protocol])
        #
        #             with open(complete_filename_eeg_setting.encode('utf-8'), 'w', newline='',
        #                       encoding='UTF-8') as outfile:
        #                 json.dump(eeg_default_setting_description, outfile, indent=4)
        #
        #         if 'emg_default_setting_id' in self.per_group_data[group_id]:
        #             emg_default_setting_description = get_emg_setting_description(self.per_group_data[group_id][
        #                                                                               'emg_default_setting_id'])
        #             emg_setting_description = "%s.json" % "emg_default_setting"
        #             complete_filename_emg_setting = path.join(directory_experimental_protocol,
        #                                                       emg_setting_description)
        #             self.files_to_zip_list.append([complete_filename_emg_setting,
        #                                            export_directory_experimental_protocol])
        #
        #             with open(complete_filename_emg_setting.encode('utf-8'), 'w', newline='',
        #                       encoding='UTF-8') as outfile:
        #                 json.dump(emg_default_setting_description, outfile, indent=4)
        #
        #         if 'tms_default_setting_id' in self.per_group_data[group_id]:
        #             tms_default_setting_description = get_tms_setting_description(self.per_group_data[group_id][
        #                                                                               'tms_default_setting_id'])
        #             tms_setting_description = "%s.json" % "tms_default_setting"
        #             complete_filename_tms_setting = path.join(directory_experimental_protocol,
        #                                                       tms_setting_description)
        #             self.files_to_zip_list.append([complete_filename_tms_setting,
        #                                            export_directory_experimental_protocol])
        #
        #             with open(complete_filename_tms_setting.encode('utf-8'), 'w', newline='',
        #                       encoding='UTF-8') as outfile:
        #                 json.dump(tms_default_setting_description, outfile, indent=4)
        #
        #         if 'context_tree_default_id' in self.per_group_data[group_id]:
        #             context_tree_default_description = get_context_tree_description(self.per_group_data[group_id][
        #                                                                                 'context_tree_default_id'])
        #             context_tree_description = "%s.json" % "context_tree_default"
        #             complete_filename_context_tree = path.join(directory_experimental_protocol,
        #                                                        context_tree_description)
        #             self.files_to_zip_list.append([complete_filename_context_tree,
        #                                            export_directory_experimental_protocol])
        #
        #             with open(complete_filename_context_tree.encode('utf-8'), 'w', newline='',
        #                       encoding='UTF-8') as outfile:
        #                 json.dump(context_tree_default_description, outfile, indent=4)
        #
        #             context_tree = get_object_or_404(ContextTree, pk=self.per_group_data[group_id][
        #                 'context_tree_default_id'])
        #             context_tree_filename = path.join(settings.BASE_DIR, "media") + "/" + context_tree.setting_file.name
        #             complete_context_tree_filename = path.join(directory_experimental_protocol,
        #                                                        context_tree.setting_file.name.split('/')[-1])
        #             with open(context_tree_filename, "rb") as f:
        #                 data = f.read()
        #             with open(complete_context_tree_filename, "wb") as f:
        #                 f.write(data)
        #
        #             self.files_to_zip_list.append([complete_context_tree_filename,
        #                                            export_directory_experimental_protocol])
        #
        #         # process participant/diagnosis per Participant of each group
        #         participant_group_list = []
        #         subject_of_group = SubjectOfGroup.objects.filter(group=group)
        #         for subject in subject_of_group:
        #             participant_group_list.append(subject.subject.patient_id)
        #
        #         if 'stimulus_data' in self.per_group_data[group_id]:
        #             stimulus_data_list = self.per_group_data[group_id]['stimulus_data']
        #             for stimulus_data in stimulus_data_list:
        #                 # ex. /Users/../qdc/media/.../NES_EXPORT/Experiment_data/Group_xxxx/Step_X_STIMULUS
        #                 path_stimulus_data = path.join(group_file_directory, stimulus_data['directory_step_name'])
        #                 if not path.exists(path_stimulus_data):
        #                     error_msg, directory_stimulus_data = create_directory(group_file_directory,
        #                                                                           stimulus_data['directory_step_name'])
        #                     if error_msg != "":
        #                         return error_msg
        #
        #                 # ex. /NES_EXPORT/Experiment_data/Group_xxxx/Step_X_STIMULUS
        #                 export_directory_stimulus_data = path.join(export_group_directory,
        #                                                            stimulus_data['directory_step_name'])
        #                 stimulus_file_name = stimulus_data['stimulus_file'].split("/")[-1]
        #                 stimulus_data_file_name = path.join(settings.BASE_DIR, "media") + "/" + \
        #                                           stimulus_data['stimulus_file']
        #                 complete_stimulus_data_filename = path.join(path_stimulus_data, stimulus_file_name)
        #
        #                 with open(stimulus_data_file_name, "rb") as f:
        #                     data = f.read()
        #
        #                 with open(complete_stimulus_data_filename, "wb") as f:
        #                     f.write(data)
        #
        #                 self.files_to_zip_list.append([complete_stimulus_data_filename, export_directory_stimulus_data])

        return error_msg

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
                'questionnaire_data_directory': '',
                'questionnaire_data_export_directory': '',
                'questionnaire_metadata_directory': '',
                'questionnaire_metadata_export_directory': '',
                'participant_data_directory': '',
                'participant_data_export_directory': '',
                'eeg_default_setting_id': '',
                'emg_default_setting_id': '',
                'tms_default_setting_id': '',
                'context_tree_default_id': ''
            }
            group_name_directory = "Group_" + group.title
            self.per_group_data[group_id]['group']['directory'] = path.join(self.get_export_directory(),
                                                                            group_name_directory)
            self.per_group_data[group_id]['group']['export_directory'] = path.join(self.get_input_data("base_directory")
                                                                                   , group_name_directory)

            self.per_group_data[group_id]['data_per_participant'] = {}
            self.per_group_data[group_id]['questionnaires_per_group'] = {}

            participant_group_list = Participant.objects.filter(group=group)
            self.per_group_data[group_id]['participant_list'] = []
            for participant in participant_group_list:
                self.per_group_data[group_id]['participant_list'].append(participant)
            participant_directory = path.join(self.per_group_data[group_id]['group']['directory'], "Participants")
            export_participant_directory = path.join(self.per_group_data[group_id]['group']['export_directory'],
                                                     "Participants")
            # participant with data collection
            eeg_participant_list = EEGData.objects.filter(participant__in=participant_group_list)
            for eeg_participant in eeg_participant_list:
                participant_code = eeg_participant.participant.code
                directory_step_name = "Step_" + str(eeg_participant.step.numeration) + "_" + \
                                      eeg_participant.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code)
                export_participant_code_directory = path.join(export_participant_directory, participant_code)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'eeg_data' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['eeg_data'] = []
                self.per_group_data[group_id]['data_per_participant'][participant_code]['eeg_data'].append({
                    'step_identification': eeg_participant.step.identification,
                    'setting_id': eeg_participant.eeg_setting_id,
                    'data_id': eeg_participant.id,
                    'directory_step_name': directory_step_name,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            emg_participant_list = EMGData.objects.filter(participant__in=participant_group_list)
            for emg_participant in emg_participant_list:
                participant_code = emg_participant.participant.code
                directory_step_name = "Step_" + str(emg_participant.step.numeration) + "_" + \
                                      emg_participant.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code)
                export_participant_code_directory = path.join(export_participant_directory, participant_code)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'emg_data' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['emg_data'] = []
                self.per_group_data[group_id]['data_per_participant'][participant_code]['emg_data'].append({
                    'step_identification': emg_participant.step.identification,
                    'setting_id': emg_participant.emg_setting_id,
                    'data_id': emg_participant.id,
                    'directory_step_name': directory_step_name,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            tms_participant_list = TMSData.objects.filter(participant__in=participant_group_list)
            for tms_participant in tms_participant_list:
                participant_code = tms_participant.participant.code
                directory_step_name = "Step_" + str(tms_participant.step.numeration) + "_" + \
                                      tms_participant.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code)
                export_participant_code_directory = path.join(export_participant_directory, participant_code)
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

            additional_data_list = AdditionalData.objects.filter(participant__in=participant_group_list)
            for additional_data in additional_data_list:
                participant_code = additional_data.participant.code
                directory_step_name = "Step_" + str(additional_data.step.numeration) + "_" + \
                                      additional_data.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code)
                export_participant_code_directory = path.join(export_participant_directory, participant_code)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'additional_data' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['additional_data'] = []
                self.per_group_data[group_id]['data_per_participant'][participant_code]['additional_data'].append({
                    'step_identification': additional_data.step.identification,
                    'setting_id': '',
                    'data_id': additional_data.id,
                    'directory_step_name': directory_step_name,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

            generic_data_list = GenericDataCollectionData.objects.filter(participant__in=participant_group_list)
            for generic_data in generic_data_list:
                participant_code = generic_data.participant.code
                directory_step_name = "Step_" + str(generic_data.step.numeration) + "_" + \
                                      generic_data.step.type.upper()
                participant_code_directory = path.join(participant_directory, participant_code)
                export_participant_code_directory = path.join(export_participant_directory, participant_code)
                if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                    self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                if 'generic_data' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['generic_data'] = []
                self.per_group_data[group_id]['data_per_participant'][participant_code]['generic_data'].append({
                    'step_identification': generic_data.step.identification,
                    'setting_id': '',
                    'data_id': generic_data.id,
                    'directory_step_name': directory_step_name,
                    'directory_step': path.join(participant_code_directory, directory_step_name),
                    'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                })

                goalkeeper_data_list = GoalkeeperGameData.objects.filter(participant__in=participant_group_list)
                for goalkeeper_data in goalkeeper_data_list:
                    participant_code = goalkeeper_data.participant.code
                    directory_step_name = "Step_" + str(goalkeeper_data.step.numeration) + "_" + \
                                          goalkeeper_data.step.type.upper()
                    participant_code_directory = path.join(participant_directory, participant_code)
                    export_participant_code_directory = path.join(export_participant_directory, participant_code)
                    if participant_code not in self.per_group_data[group_id]['data_per_participant']:
                        self.per_group_data[group_id]['data_per_participant'][participant_code] = {}
                    if 'goalkeeper_data' not in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        self.per_group_data[group_id]['data_per_participant'][participant_code]['goalkeeper_data'] = []
                    self.per_group_data[group_id]['data_per_participant'][participant_code]['goalkeeper_data'].append({
                        'step_identification': goalkeeper_data.step.identification,
                        'setting_id': '',
                        'data_id': goalkeeper_data.id,
                        'directory_step_name': directory_step_name,
                        'directory_step': path.join(participant_code_directory, directory_step_name),
                        'export_directory_step': path.join(export_participant_code_directory, directory_step_name),
                    })

                # stimulus_data_list = Step.objects.filter(type='stimulus')

        return error_msg

    def download_data_per_participant(self):
        error_msg = ""
        for group_id in self.per_group_data:
            if 'data_per_participant' in self.per_group_data[group_id]:
                group_directory = self.per_group_data[group_id]['group']['directory']

                # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants
                error_msg, group_participants_directory = create_directory(group_directory, "Participants")
                if error_msg != "":
                    return error_msg
                # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants
                export_directory_group = self.per_group_data[group_id]['group']['export_directory']
                export_directory_group_participants = path.join(export_directory_group, "Participants")
                for participant_code in self.per_group_data[group_id]['data_per_participant']:
                    # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXXX
                    error_msg, participant_directory = create_directory(group_participants_directory, participant_code)
                    if error_msg != "":
                        return error_msg
                    # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX
                    export_directory_participant = path.join(export_directory_group_participants, participant_code)
                    if 'eeg_data' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        eeg_data_list = self.per_group_data[group_id]['data_per_participant'][participant_code][
                            'eeg_data']
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

                            eeg_data = get_object_or_404(EEGData, pk=eeg_data['data_id'])
                            # download eeg raw data file
                            eeg_data_filename = eeg_data.file.file.name.split('/')[-1]
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EEG/eeg.raw
                            complete_eeg_data_filename = path.join(eeg_directory, eeg_data_filename)
                            eeg_raw_data_file = path.join(path.join(settings.BASE_DIR, "media/"),
                                                          eeg_data.file.file.name)

                            with open(eeg_raw_data_file, 'rb') as f:
                                data = f.read()

                            with open(complete_eeg_data_filename, 'wb') as f:
                                f.write(data)

                            self.files_to_zip_list.append([complete_eeg_data_filename, export_eeg_directory])

                            # download eeg_setting_description
                            eeg_setting_description = get_eeg_setting_description(eeg_data.eeg_setting_id)
                            eeg_setting_filename = "%s_%s.json" % (eeg_data_filename.split(".")[0],
                                                                   "setting_description")

                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EEG/
                            # eeg_rawfilename_setting_description.json#
                            complete_setting_filename = path.join(eeg_directory, eeg_setting_filename)

                            self.files_to_zip_list.append([complete_setting_filename, export_eeg_directory])

                            with open(complete_setting_filename.encode('utf-8'), 'w', newline='',
                                      encoding='UTF-8') as outfile:
                                json.dump(eeg_setting_description, outfile, indent=4)

                    if 'emg_data' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        emg_data_list = self.per_group_data[group_id]['data_per_participant'][participant_code][
                            'emg_data']
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

                            emg_data = get_object_or_404(EMGData, pk=emg_data['data_id'])
                            # download emg raw data file
                            emg_data_filename = emg_data.file.file.name.split('/')[-1]
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EMG/emg.raw
                            complete_emg_data_filename = path.join(emg_directory, emg_data_filename)
                            emg_raw_data_file = path.join(path.join(settings.BASE_DIR, "media/"),
                                                          emg_data.file.file.name)

                            with open(emg_raw_data_file, 'rb') as f:
                                data = f.read()

                            with open(complete_emg_data_filename, 'wb') as f:
                                f.write(data)

                            self.files_to_zip_list.append([complete_emg_data_filename, export_emg_directory])

                            # download emg_setting_description
                            emg_setting_description = get_emg_setting_description(emg_data.emg_setting_id)
                            emg_setting_filename = "%s_%s.json" % (emg_data_filename.split(".")[0],
                                                                   "setting_description")

                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_EMG/
                            # emg_rawfilename_setting_description.json#
                            complete_setting_filename = path.join(emg_directory, emg_setting_filename)

                            self.files_to_zip_list.append([complete_setting_filename, export_emg_directory])

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
                    if 'additional_data' in self.per_group_data[group_id]['data_per_participant'][participant_code]:
                        additional_data_list = self.per_group_data[group_id]['data_per_participant'][
                            participant_code]['additional_data']
                        for additional_data in additional_data_list:
                            additional_data_directory = additional_data['directory_step']
                            # ex. Users/.../EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_step_TYPE
                            if not path.exists(additional_data_directory):
                                error_msg, additional_data_directory = create_directory(
                                    participant_directory, additional_data['directory_step_name'])
                                if error_msg != "":
                                    return error_msg
                            # ex. EXPERIMENT_DOWNLOAD/Group_group.title/Participants/PXXXX/Step_XX_step_TYPE
                            export_additional_data_directory = additional_data['export_directory_step']

                            data_file = get_object_or_404(AdditionalData, pk=additional_data['data_id'])
                            file_name = data_file.file.file.name.split('/')[-1]
                            # read file from repository
                            additional_data_filename = path.join(settings.BASE_DIR, 'media') + '/' + \
                                                       data_file.file.file.name

                            # ex. /Users/.../NES_EXPORT/Experiment_data/Group_XXX/Participants/PXXXX/
                            # Step_XX_step_TYPE/file_name.format_type
                            complete_additional_data_filename = path.join(additional_data_directory, file_name)
                            with open(additional_data_filename, 'rb') as f:
                                data = f.read()

                            with open(complete_additional_data_filename, 'wb') as f:
                                f.write(data)

                            self.files_to_zip_list.append([complete_additional_data_filename,
                                                           export_additional_data_directory])

        return error_msg


def get_eeg_setting_description(eeg_setting_id):
    eeg_setting = get_object_or_404(EEGSetting, pk=eeg_setting_id)
    description = {
        'name': eeg_setting.name,
        'description': eeg_setting.description,
    }
        # description['eeg_amplifier_setting'] = []
        # eeg_amplifier_setting = eeg_setting.eeg_amplifier_setting
        # description['eeg_amplifier_setting'].append({
        #     'identification': eeg_amplifier_setting.eeg_amplifier.identification,
        #     'description': eeg_amplifier_setting.eeg_amplifier.description,
        #     'gain': eeg_amplifier_setting.gain,
        #     'sampling_rate': eeg_amplifier_setting.sampling_rate,
        #     'number_of_channels_used': eeg_amplifier_setting.number_of_channels_used
        # })
        #
        # description['eeg_filter_setting'] = []
        # eeg_filter_setting = eeg_setting.eeg_filter_setting
        # description['eeg_filter_setting'].append({
        #     'filter_type': eeg_filter_setting.eeg_filter_type.name,
        #     'description': eeg_filter_setting.eeg_filter_type.description,
        #     'high_pass': eeg_filter_setting.high_pass,
        #     'low_pass': eeg_filter_setting.low_pass,
        #     'order': eeg_filter_setting.order,
        #     'high_band_pass': eeg_filter_setting.high_band_pass,
        #     'low_band_pass': eeg_filter_setting.low_band_pass,
        #     'high_notch': eeg_filter_setting.high_notch,
        #     'low_notch': eeg_filter_setting.low_notch
        # })
        #
        # description['eeg_solution_setting'] = []
        # eeg_solution_setting = eeg_setting.eeg_solution_setting
        # description['eeg_solution_setting'].append({
        #     'manufacturer': eeg_solution_setting.eeg_solution.manufacturer.name,
        #     'identification': eeg_solution_setting.eeg_solution.name,
        #     'components': eeg_solution_setting.eeg_solution.components
        # })
        #
        # description['eeg_electrode_layout_setting'] = []
        # eeg_electrode_layout_setting = eeg_setting.eeg_electrode_layout_setting.eeg_electrode_net_system
        # description['eeg_electrode_layout_setting'].append({
        #     'manufacturer': eeg_electrode_layout_setting.eeg_electrode_net.manufacturer.name,
        #     'identification': eeg_electrode_layout_setting.eeg_electrode_net.identification,
        #     'description': eeg_electrode_layout_setting.eeg_electrode_net.description,
        #     'eeg_electrode_localization_system': eeg_electrode_layout_setting.eeg_electrode_localization_system.name,
        #     'eeg_electrode_model_default': eeg_electrode_layout_setting.eeg_electrode_localization_system.name,
        #     'cap_size': ''
        # })

    return description


def get_emg_setting_description(emg_setting_id):
    emg_setting = get_object_or_404(EMGSetting, pk=emg_setting_id)

    emg_description = {
        'setting_description': {},
        'ad_converter_setting': {},
        'digital_filter_setting': {}
    }

    emg_description['setting_description'] = {
        'name': emg_setting.name,
        'description': emg_setting.description,
        'acquisition_software_version': emg_setting.acquisition_software_version
    }

    # emg_description['ad_converter_setting'] = {
    #     'sampling_rate': emg_setting.emg_ad_converter_setting.sampling_rate,
    # }

    # emg_digital_filter_setting = emg_setting.emg_digital_filter_setting
    # emg_description['digital_filter_setting'] = {
    #     'high_pass': emg_digital_filter_setting.high_pass,
    #     'low_pass': emg_digital_filter_setting.low_pass,
    #     'order': emg_digital_filter_setting.order,
    #     'high_band_pass': emg_digital_filter_setting.high_band_pass,
    #     'low_band_pass': emg_digital_filter_setting.low_band_pass,
    #     'high_notch': emg_digital_filter_setting.high_notch,
    #     'low_notch': emg_digital_filter_setting.low_notch
    # }

    return emg_description


def get_tms_data_description(tms_data_id):
    tms_data = get_object_or_404(TMSData, pk=tms_data_id)

    tms_description = {
        'setting_description': {},
        'stimulation_description': {},
        'hotspot_position': {},
    }

    tms_description['stimulation_description'] = {
        'tms_stimulation_description': tms_data.description,
        # 'pulse_stimulus': tms_data.tms_setting.tms_device_setting.pulse_stimulus_type,
        'resting_motor threshold-RMT(%)': tms_data.resting_motor_threshold,
        'test_pulse_intensity_of_simulation(% over the %RMT)': tms_data.test_pulse_intensity_of_simulation,
        'interval_between_pulses': tms_data.interval_between_pulses,
        'interval_between_pulses_unit': tms_data.interval_between_pulses_unit,
        'repetitive_pulse_frequency': tms_data.repetitive_pulse_frequency,
        'coil_orientation': tms_data.coil_orientation,
        'coil_orientation_angle': tms_data.coil_orientation_angle,
        'second_test_pulse_intensity (% over the %RMT)': tms_data.second_test_pulse_intensity,
        'time_between_mep_trials': tms_data.time_between_mep_trials,
        'time_between_mep_trials_unit': tms_data.time_between_mep_trials_unit,
    }
    # localization_system_selected = get_object_or_404(TMSLocalizationSystem,
    #                                                  pk=tms_data.hotspot.tms_localization_system_id)
    tms_description['hotspot_position'] = {
        'tms_localization_system_name': tms_data.localization_system_name,
        'tms_localization_system_description': tms_data.localization_system_description,
        'brain_area': tms_data.brain_area_name,
        'brain_area_system_name': tms_data.brain_area_system_name,
        'brain_area_system_description': tms_data.brain_area_system_description
    }

    # tms_setting = get_object_or_404(TMSSetting, pk=tms_data.tms_setting_id)
    #
    # tms_description['setting_description'] = {
    #     'name': tms_setting.name,
    #     'description': tms_setting.description,
    #     'pulse_stimulus_type': tms_setting.tms_device_setting.pulse_stimulus_type,
    # }
    #
    return tms_description


def get_tms_setting_description(tms_setting_id):
    tms_setting = get_object_or_404(TMSSetting, pk=tms_setting_id)

    tms_setting_description = {
        'name': tms_setting.name,
        'description': tms_setting.description,
        # 'tms_device': tms_setting.tms_device_setting.coil_model.name,
        # 'tms_device': tms_setting.tms_device_setting.tms_device.manufacturer.name,
        # 'tms_device_description': tms_setting.tms_device_setting.tms_device.description,
        # 'coil_model_description': tms_setting.tms_device_setting.coil_model.description,
        # 'coil_model_design': tms_setting.tms_device_setting.coil_model.coil_design,
        # 'pulse_stimulus_type': tms_setting.tms_device_setting.pulse_stimulus_type,
    }

    return tms_setting_description


def get_context_tree_description(context_tree_id):
    context_tree = get_object_or_404(ContextTree, pk=context_tree_id)
    context_tree_description = {
        'name': context_tree.name,
        'description': context_tree.description,
        'setting_text': context_tree.setting_text,
    }

    return context_tree_description
