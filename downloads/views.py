import os
import re
import tempfile
import shutil
import subprocess
import time
import zipfile

from os import path
from shutil import rmtree
from zipfile import ZipFile

import sys
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_str
from django.utils.text import slugify
from django.utils.translation import ugettext as _

from .export import create_directory, ExportExecution
from .input_export import build_complete_export_structure
from .models import Export
from experiments.models import Experiment, Group, Step, Participant

JSON_FILENAME = "json_export.json"
JSON_EXPERIMENT_FILENAME = "json_experiment_export.json"
EXPORT_DIRECTORY = "temp"
DOWNLOAD_DIRECTORY = "download"
EXPORT_FILENAME = "download.zip"
EXPORT_EXPERIMENT_FILENAME = "download_experiment.zip"
DOWNLOAD_ERROR_MESSAGE = _('There was a problem downloading your experiment '
                           'data')


# Create your views here.
def create_export_instance():
    export_instance = Export()
    export_instance.save()

    return export_instance


def remove_files(archive, request, experiment):
    """Remove experiment data from archive
    :param archive: compressed file from what build partial download
    :param request: request object
    :param experiment: Experiment model object
    :return: archive with entries reduced if success else empty string
    """
    partial_download = os.path.join(
        path.dirname(archive),
        'partial_download_' + str(int(time.time())) + '.zip'
    )
    try:
        shutil.copyfile(archive, partial_download)
    except FileNotFoundError:
        return ''

    subdirs = [
        os.path.join('EXPERIMENT_DOWNLOAD', 'Experiment.csv'),
        os.path.join('EXPERIMENT_DOWNLOAD', 'LICENSE.txt'),
        os.path.join('EXPERIMENT_DOWNLOAD', 'CITATION.txt')
    ]
    for subdir in request.POST.getlist('download_selected'):
        # take the group title to copy subdirs/files to temp location
        group_str = re.search("g[0-9]+", subdir)
        group_id = int(group_str.group(0)[1:])
        group = Group.objects.get(pk=group_id)
        group_title_slugifyed = slugify(group.title)
        # Options values in templates has group and/or participants id's as
        # substrings, so use regex to determine if they were selected.
        pattern_exp_protocol = re.compile("experimental_protocol_g[0-9]+$")
        pattern_questionnaires = re.compile("questionnaires_g[0-9]+$")
        pattern_participant = re.compile("participant_p[0-9]+_g[0-9]+$")

        if pattern_exp_protocol.match(subdir):
            subdirs.append(
                os.path.join(
                    'EXPERIMENT_DOWNLOAD',
                    'Group_' + group_title_slugifyed,
                    'Experimental_protocol'
                )
            )
        if pattern_questionnaires.match(subdir):
            subdirs.append(
                os.path.join(
                    'EXPERIMENT_DOWNLOAD',
                    'Group_' + group_title_slugifyed,
                    'Per_questionnaire_data'
                )
            )
            subdirs.append(
                os.path.join(
                    'EXPERIMENT_DOWNLOAD',
                    'Group_' + group_title_slugifyed,
                    'Participants.csv'
                )
            )
        if pattern_participant.match(subdir):
            # Add Per_participant_data subdir for the specific group in temp
            # dir.
            participant_str = re.search("p[0-9]+", subdir)
            participant_id = int(participant_str.group(0)[1:])
            participant = Participant.objects.get(pk=participant_id)
            # If g1 == g2 in test_views, this subtree may already has been
            # created.
            # TODO: fix test. Probably chosing participants from
            # TODO: diferent groups, as it's the case when selecting
            # TODO: participants to download in UI.
            subdirs.append(
                os.path.join(
                    'EXPERIMENT_DOWNLOAD',
                    'Group_' + group_title_slugifyed,
                    'Per_participant_data',
                    'Participant_' + participant.code
                )
            )

    # questionnaire_metadata goes for all groups that have questionnaires
    for group in experiment.groups.all():
        if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
            group_title_slugifyed = slugify(group.title)
            subdirs.append(
                os.path.join(
                    'EXPERIMENT_DOWNLOAD',
                    'Group_' + group_title_slugifyed,
                    'Questionnaire_metadata'
                )
            )

    # subtracts files that will not go in compressed file based in user choices
    zip_file = zipfile.ZipFile(partial_download)
    zip_file_set = set(zip_file.namelist())
    for subdir in subdirs:
        r = re.compile(subdir)
        sub_set = set(filter(r.match, zip_file_set))
        if not sub_set:
            os.remove(partial_download)
            return ''
        zip_file_set -= sub_set
    cmd = ['zip', '-d', partial_download] + list(zip_file_set)

    # if testing or running jenkins, redirects stdout to a temp file
    try:
        if 'test' in sys.argv or 'jenkins' in sys.argv or 'runserver' in sys.argv:
            subprocess.check_call(
                cmd, stdout=tempfile.NamedTemporaryFile(suffix='.txt')
            )
        else:
            subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        messages.error(request, DOWNLOAD_ERROR_MESSAGE)
        return ''

    return partial_download


def download_view(request, experiment_id):
    experiment = get_object_or_404(Experiment, pk=experiment_id)
    compressed_file = os.path.join(
        settings.MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
    )

    if request.method == 'POST':
        # If user selected nothing, just redirect to experiment detail view
        # with warning message
        if 'download_selected' not in request.POST:
            messages.warning(request, _('Please select item(s) to download'))
            return HttpResponseRedirect(
                reverse('experiment-detail', kwargs={'slug': experiment.slug})
            )

        compressed_file = remove_files(compressed_file, request, experiment)
        if not compressed_file:
            messages.error(request, DOWNLOAD_ERROR_MESSAGE)
            return HttpResponseRedirect(
                reverse('experiment-detail', kwargs={'slug': experiment.slug})
            )
    try:
        file = open(compressed_file, 'rb')
    except FileNotFoundError:
        messages.error(request, DOWNLOAD_ERROR_MESSAGE)
        return HttpResponseRedirect(
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )

    if 'test' in sys.argv or 'jenkins' in sys.argv or 'runserver' in sys.argv:
        response = HttpResponse(file, content_type='application/zip')
        response['Content-Length'] = path.getsize(compressed_file)
    else:
        response = HttpResponse(content_type='application/force-download')
        response['X-Sendfile'] = smart_str(compressed_file)
        response['Content-Length'] = path.getsize(compressed_file)
        response['Set-Cookie'] = 'fileDownload=true; path=/'
    response['Content-Disposition'] = \
        'attachment; filename=%s' % smart_str('download.zip')
    file.close()

    # TODO: updates download counter only if not logged in
    experiment.downloads += 1
    experiment.save()

    return response


def get_export_instance(export_id):
    export_instance = Export.objects.get(id=export_id)

    return export_instance


def update_export_instance(input_file, output_export, export_instance):
    export_instance.input_file = input_file
    export_instance.output_export = output_export
    export_instance.save()


def download_create(experiment_id, template_name):
    try:
        export_instance = create_export_instance()  # TODO: remove this method
        input_export_file = path.join(
            EXPORT_DIRECTORY, str(export_instance.id), str(JSON_FILENAME)
        )
        input_filename = path.join(settings.MEDIA_ROOT, input_export_file)
        create_directory(settings.MEDIA_ROOT, path.split(input_export_file)[0])
        build_complete_export_structure(experiment_id, input_filename)
        export = ExportExecution(experiment_id)

        # set path of the directory base: ex. /media/temp/
        base_directory, path_to_create = \
            path.split(export.get_directory_base())
        error_msg, base_directory_name = create_directory(
            base_directory, path_to_create
        )
        if error_msg != "":
            return error_msg

        # prepare data to be processed
        input_data = export.read_configuration_data(input_filename)

        if not export.is_input_data_consistent() or not input_data:
            error_msg = "Inconsistent data read from json file"
        if error_msg != "":
            return error_msg

        # Load information of the data collection per participant in a
        # dictionnary.
        error_msg = export.include_data_from_group(experiment_id)
        if error_msg != "":
            return error_msg

        # Create export files
        # Create files of experimental protocol and diagnosis/participant
        # csv file for each group.
        error_msg = export.process_experiment_data(experiment_id)
        if error_msg != "":
            return error_msg

        # process the data per participant
        error_msg = export.download_data_per_participant()
        if error_msg != "":
            return error_msg

        # process the data per questionnaire
        error_msg = export.download_data_per_questionnaire()

        # create zip file and include files
        if export.files_to_zip_list:
            # 'download.zip'
            export_filename = export.get_input_data("export_filename")
            export_complete_filename = path.join(
                base_directory_name, export_filename
            )

            with ZipFile(export_complete_filename, 'w') as zip_file:
                for filename, directory in export.files_to_zip_list:
                    fdir, fname = path.split(filename)
                    zip_file.write(
                        filename.encode('utf-8'), path.join(directory, fname)
                    )

        export_instance_directory = settings.MEDIA_ROOT + '/'
        temp_directory = path.join(
            export_instance_directory,
            path.join(EXPORT_DIRECTORY, str(export_instance.id))
        )
        rmtree(temp_directory, ignore_errors=True)

        if template_name != "":
            return error_msg

    except OSError as e:
        print(e)
        error_msg = e
        if template_name != "":
            return error_msg
