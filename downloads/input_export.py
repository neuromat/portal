# -*- coding: utf-8 -*-
from json import dump, load

BASE_DIRECTORY = "EXPERIMENT_DOWNLOAD"
PER_PARTICIPANT_DIRECTORY = "Per_participant_data"
PER_QUESTIONNAIRE_DIRECTORY = "Per_questionnaire_data"
QUESTIONNAIRE_METADATA_DIRECTORY = "Questionnaire_metadata"
PARTICIPANT_DATA_DIRECTORY = "Per_participant_data"
EXPERIMENT_DATA_DIRECTORY = "Experiment_data"
EXPORT_FILENAME = "download.zip"
EXPORT_EXPERIMENT_FILENAME = "download_experiment.zip"
EXPORT_PER_PARTICIPANT = 1
EXPORT_PER_QUESTIONNAIRE = 1
DEFAULT_LANGUAGE = "pt-BR"
PREFIX_FILENAME_FIELDS = "Fields"
PREFIX_FILENAME_RESPONSES = "Responses"
OUTPUT_FILENAME_PARTICIPANTS = "Participants"
OUTPUT_FILENAME_DIAGNOSIS = "Diagnosis"


class InputExport:
    def __init__(self):
        self.data = {}

    def read(self, input_filename, update_input_data=True):
        print("read")

        with open(input_filename.encode('utf-8'), 'r') as input_file:
            input_data_temp = load(self.data, input_file)

            if update_input_data:
                self.data = input_data_temp

        return self.data

    def write(self, output_filename):
        with open(output_filename.encode('utf-8'), 'w', encoding='UTF-8') as outfile:
            dump(self.data, outfile)

    def build_header(self, export_per_experiment):
        # /NES_EXPORT
        self.data["base_directory"] = BASE_DIRECTORY
        self.data["per_participant_directory"] = PER_PARTICIPANT_DIRECTORY
        self.data["per_questionnaire_directory"] = PER_QUESTIONNAIRE_DIRECTORY
        self.data["questionnaire_metadata_directory"] = QUESTIONNAIRE_METADATA_DIRECTORY
        self.data["export_filename"] = EXPORT_FILENAME
        if export_per_experiment:
            self.data["experiment_data_directory"] = EXPERIMENT_DATA_DIRECTORY
            self.data["participant_data_directory"] = PARTICIPANT_DATA_DIRECTORY

    def build_dynamic_header(self, variable_name, variable_data):
        self.data[variable_name] = variable_data

    def build_diagnosis_participant(self, strut_name, output_filename, field_header_list):
        print("participant or diagnosis")
        self.data[strut_name] = []
        self.data[strut_name].append({"output_filename": output_filename, "output_list": [], "data_list": []})

        for field, header in field_header_list:
            output_data = {"header": header, "field": field}
            self.data[strut_name][0]["output_list"].append(output_data)


def build_partial_export_structure(export_per_participant, participant_field_header_list, output_filename,
                                   language=DEFAULT_LANGUAGE):

    json_data = InputExport()

    json_data.build_header()
    json_data.build_dynamic_header("export_per_participant", export_per_participant)
    json_data.build_diagnosis_participant("participants", OUTPUT_FILENAME_PARTICIPANTS, participant_field_header_list)
    json_data.write(output_filename)


def build_complete_export_structure(experiment_id, output_filename, language=DEFAULT_LANGUAGE):

    json_data = InputExport()

    json_data.build_header(True)

    json_data.build_dynamic_header("export_per_participant", True)

    json_data.build_dynamic_header("export_per_questionnaire", True)

    json_data.build_dynamic_header("response_type", None)

    json_data.build_dynamic_header("heading_type", None)

    json_data.data["questionnaire_list"] = []

    json_data.write(output_filename)
