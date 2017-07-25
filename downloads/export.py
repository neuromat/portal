import json
from os import path, makedirs
from csv import writer
from django.conf import settings
from django.shortcuts import get_object_or_404

from experiments.models import Experiment, Group, Participant, EEGData, EMGData

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

    def set_directory_base(self, user_id, export_id):
        self.directory_base = path.join(self.base_directory_name, str(user_id))
        self.directory_base = path.join(self.directory_base, str(export_id))

    def get_directory_base(self):

        return self.directory_base  # MEDIA_ROOT/download/username_id/export_id

    def __init__(self, user_id, export_id):
        # self.get_session_key()

        # questionnaire_id = 0
        self.files_to_zip_list = []
        # self.headers = []
        # self.fields = []
        self.directory_base = ''
        self.base_directory_name = path.join(settings.MEDIA_ROOT, "download")
        # self.directory_base = self.base_directory_name
        self.set_directory_base(user_id, export_id)
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
        experiment_resume_header = 'Study' + '\t' + 'Study description' + '\t' + 'Start date' + '\t' + \
                                   'End date' + '\t' + 'Experiment' + '\t' + \
                                   'Experiment description' + '\t' + "\n"
        experiment_resume = \
            study.title + '\t' + study.description + '\t' + \
            str(study.start_date) + '\t' + str(study.end_date) + '\t' + \
            experiment.title + '\t' + experiment.description + '\t' + "\n"

        filename_experiment_resume = "%s.csv" % "Experiment"

        # path ex. /EXPERIMENT_DOWNLOAD/Experiment_data
        # export_experiment_data = path.join(self.get_input_data("base_directory"),
        #                                    self.get_input_data("experiment_data_directory"))
        # path ex. /EXPERIMENT_DOWNLOAD/
        export_experiment_data = self.get_input_data("base_directory")

        # path ex. UserS/.../qdc/media/.../EXPERIMENT_DOWNLOAD/Experiment_data
        # experiment_resume_directory = path.join(self.get_export_directory(),
        #                                         self.get_input_data("experiment_data_directory"))
        # # path ex. UserS/.../qdc/media/.../EXPERIMENT_DOWNLOAD/
        experiment_resume_directory = self.get_export_directory()
        # Users/.../qdc/media/.../EXPERIMENT_DOWNLOAD/Experiment.csv
        complete_filename_experiment_resume = path.join(experiment_resume_directory, filename_experiment_resume)

        self.files_to_zip_list.append([complete_filename_experiment_resume, export_experiment_data])

        with open(complete_filename_experiment_resume.encode('utf-8'), 'w', newline='',
                  encoding='UTF-8') as csv_file:
            csv_file.writelines(experiment_resume_header)
            csv_file.writelines(experiment_resume)

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

                    with open(complete_filename_experimental_protocol.encode('utf-8'), 'w', newline='', encoding='UTF-8') \
                            as txt_file:
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
                participant_list = Participant.objects.filter(group=group)
                # participant with data collection
                eeg_participant_list = EEGData.objects.filter(participant__in=participant_list).values('participant_id')
                emg_participant_list = EMGData.objects.filter(participant__in=participant_list).values('participant_id')
                header_personal_data = ["Participant_code", "Age", "Gender"]
                personal_data_list = []
                for participant in participant_list:
                    # save personal data
                    data = [participant.code, participant.age, participant.gender]
                    personal_data_list.append(data)

                personal_data_list.insert(0, header_personal_data)
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