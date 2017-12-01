import os
import re
import tempfile
import shutil

from os import path
from shutil import rmtree
from zipfile import ZipFile
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_str
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


def download_view(request, experiment_id):
    experiment = get_object_or_404(Experiment, pk=experiment_id)

    # If it's a get request, serve file with all experiment data immediatally
    # for download.
    if request.method == 'GET':
        compressed_file = os.path.join(
            settings.MEDIA_ROOT, 'download', str(experiment.id), 'download.zip'
        )
        try:
            zip_file = open(compressed_file, 'rb')
        except FileNotFoundError:
            messages.error(request, DOWNLOAD_ERROR_MESSAGE)
            return HttpResponseRedirect(
                reverse('experiment-detail', kwargs={'slug': experiment.slug})
            )
        response = HttpResponse(content_type='application/force-download')
        response['Content-Disposition'] = \
            'attachment; filename=%s' % smart_str('download.zip')
        response['X-Sendfile'] = smart_str(compressed_file)
        response['Content-Length'] = path.getsize(compressed_file)
        response['Set-Cookie'] = 'fileDownload=true; path=/'
        zip_file.close()

        experiment.downloads += 1
        experiment.save()

        return response

    # If user selected nothing, just redirect to experiment detail view with
    # warning message.
    if 'download_selected' not in request.POST:
        messages.warning(request, _('Please select item(s) to download'))
        return HttpResponseRedirect(
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )

    ##
    # Create compressed file with elements chosen by user
    # ---------------------------------------------------
    # TODO: if experiment has no groups return response with only
    # TODO: Experiments.csv
    # create temporary dir to aggregate subdirs/files for further
    # incorporate in compacted file
    temp_dir = tempfile.mkdtemp()
    # Experiment.csv always will be in compressed file
    try:
        shutil.copyfile(os.path.join(
            settings.MEDIA_ROOT, 'download', str(experiment.id),
            'Experiment.csv'
        ), os.path.join(temp_dir, 'Experiment.csv')
        )
    except FileNotFoundError:
        messages.error(request, DOWNLOAD_ERROR_MESSAGE)
        return HttpResponseRedirect(
            reverse('experiment-detail', kwargs={'slug': experiment.slug})
        )

    # Copy experiment data from settings.MEDIA_ROOT/download/<experiment.id>
    # based on user selection, to temp dir.
    for item in request.POST.getlist('download_selected'):
        # take the group title to copy subdirs/files to temp location
        group_str = re.search("g[0-9]+", item)
        group_id = int(group_str.group(0)[1:])
        group = Group.objects.get(pk=group_id)
        # Options values in templates has group and/or participants id's as
        # substrings, so use regex to determine if they were selected.
        pattern_exp_protocol = re.compile("experimental_protocol_g[0-9]+$")
        pattern_questionnaires = re.compile("questionnaires_g[0-9]+$")
        pattern_participant = re.compile("participant_p[0-9]+_g[0-9]+$")
        if pattern_exp_protocol.match(item):
            # add Experimental_protocol subdir for the specific group in temp
            # dir
            try:
                shutil.copytree(os.path.join(
                    settings.MEDIA_ROOT, 'download', str(experiment.id),
                    'Group_' + group.title, 'Experimental_protocol'
                ), os.path.join(temp_dir, 'Group_' + group.title,
                                'Experimental_protocol')
                )
            except FileNotFoundError:
                messages.error(request, DOWNLOAD_ERROR_MESSAGE)
                return HttpResponseRedirect(
                    reverse('experiment-detail',
                            kwargs={'slug': experiment.slug})
                )
        if pattern_questionnaires.match(item):
            # Add Per_questionnaire_data subdir for the specific group in temp
            # dir.
            try:
                shutil.copytree(os.path.join(
                    settings.MEDIA_ROOT, 'download', str(experiment.id),
                    'Group_' + group.title, 'Per_questionnaire_data'
                ), os.path.join(temp_dir, 'Group_' + group.title,
                                'Per_questionnaire_data')
                )
            except FileNotFoundError:
                messages.error(request, DOWNLOAD_ERROR_MESSAGE)
                return HttpResponseRedirect(
                    reverse('experiment-detail',
                            kwargs={'slug': experiment.slug})
                )
            # add Participants.csv file for the specific group in temp dir.
            try:
                shutil.copyfile(os.path.join(
                    settings.MEDIA_ROOT, 'download', str(experiment.id),
                    'Group_' + group.title, 'Participants.csv'
                ), os.path.join(temp_dir, 'Group_' + group.title,
                                'Participants.csv')
                )
            except FileNotFoundError:
                messages.error(request, DOWNLOAD_ERROR_MESSAGE)
                return HttpResponseRedirect(
                    reverse('experiment-detail',
                            kwargs={'slug': experiment.slug})
                )
        if pattern_participant.match(item):
            # Add Per_participant_data subdir for the specific group in temp
            # dir.
            participant_str = re.search("p[0-9]+", item)
            participant_id = int(participant_str.group(0)[1:])
            participant = Participant.objects.get(pk=participant_id)
            # If g1 == g2 in test_views, this subtree may already has been
            # created.
            # TODO: fix test. Probably chosing participants from
            # TODO: diferent groups, as it's the case when selecting
            # TODO: participants to download in UI.
            try:
                shutil.copytree(os.path.join(
                    settings.MEDIA_ROOT, 'download', str(experiment.id),
                    'Group_' + group.title, 'Per_participant_data', 
                    'Participant_' + participant.code
                ), os.path.join(temp_dir, 'Group_' + group.title,
                                'Per_participant_data', 'Participant_' +
                                participant.code)
                )
            except FileNotFoundError:
                messages.error(request, DOWNLOAD_ERROR_MESSAGE)
                return HttpResponseRedirect(
                    reverse('experiment-detail',
                            kwargs={'slug': experiment.slug})
                )

    # Put Questionnaire_metadata subdir in temp dir for all groups that have
    # questionnaires.
    for group in experiment.groups.all():
        if group.steps.filter(type=Step.QUESTIONNAIRE).count() > 0:
            try:
                shutil.copytree(os.path.join(
                    settings.MEDIA_ROOT, 'download', str(experiment.id),
                    'Group_' + group.title, 'Questionnaire_metadata'
                ), os.path.join(temp_dir, 'Group_' + group.title,
                                'Questionnaire_metadata')
                )
            except FileNotFoundError:
                messages.error(request, DOWNLOAD_ERROR_MESSAGE)
                return HttpResponseRedirect(
                    reverse('experiment-detail',
                            kwargs={'slug': experiment.slug})
                )

    # make compressed file and return response to client
    compressed_file = shutil.make_archive(os.path.join(
        tempfile.mkdtemp(), 'download'), 'zip', temp_dir
    )
    response = HttpResponse(content_type='application/force-download')
    response['Content-Disposition'] = \
        'attachment; filename=%s' % smart_str('download.zip')
    response['X-Sendfile'] = smart_str(compressed_file)
    response['Content-Length'] = path.getsize(compressed_file)
    response['Set-Cookie'] = 'fileDownload=true; path=/'

    experiment.downloads += 1
    experiment.save()

    return response

    template_name = "experiments/detail.html"
    error_msg = download_create(experiment_id, template_name)

    if error_msg != "":
        messages.error(request, error_msg)
        return render(request, template_name)
    else:
        messages.success(request, "Download was finished correctly")
        return render(request, template_name)


    # if complete_filename:
    #
    #     messages.success(request, "Download was finished correctly")
    #
    #     # print("antes do fim: httpResponse")
    #     #
    #     zip_file = open(complete_filename, 'rb')
    #
    #     response = HttpResponse(zip_file, content_type='application/zip')
    #     response['Content-Disposition'] = 'attachment; filename="export.zip"'
    #     response['Content-Length'] = path.getsize(complete_filename)
    #     response['Set-Cookie'] = 'fileDownload=true; path=/'
    #     response['slug'] = experiment.slug
    #     return response
    #     else:
        #     messages.error(request, "Download data was not generated.")
        #     return HttpResponseRedirect(template_name, args=(experiment.slug,))


def get_export_instance(export_id):
    export_instance = Export.objects.get(id=export_id)

    return export_instance


def update_export_instance(input_file, output_export, export_instance):
    export_instance.input_file = input_file
    export_instance.output_export = output_export
    export_instance.save()


def download_create(experiment_id, template_name):
    try:
        export_instance = create_export_instance()

        input_export_file = path.join(EXPORT_DIRECTORY,
                                      path.join(path.join(str(export_instance.id), str(JSON_FILENAME))))

        input_filename = path.join(settings.MEDIA_ROOT, input_export_file)

        create_directory(settings.MEDIA_ROOT, path.split(input_export_file)[0])

        build_complete_export_structure(experiment_id, input_filename)

        export = ExportExecution(experiment_id)

        # set path of the directory base: ex. /Users/.../portal/media/temp/
        base_directory, path_to_create = path.split(export.get_directory_base())
        # ex. /Users/.../portal/media/download/experiment_id
        error_msg, base_directory_name = create_directory(base_directory, path_to_create)
        if error_msg != "":
            return error_msg

        # # ex. /Users/.../portal/media/temp/export_instance.id/json_export.json
        # input_export_file = path.join("export", path.join(path.join(str(export_instance.id), str(input_filename))))

        # prepare data to be processed
        input_data = export.read_configuration_data(input_filename)

        if not export.is_input_data_consistent() or not input_data:
            error_msg = "Inconsistent data read from json file"
        if error_msg != "":
            return error_msg

        # load information of the data collection per participant in a dictionnary
        error_msg = export.include_data_from_group(experiment_id)
        if error_msg != "":
            return error_msg

        # Create arquivos para exportação
        # create files of experimental protocol and diagnosis/participant csv file for each group
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
            export_filename = export.get_input_data("export_filename")  # 'download.zip'
            export_complete_filename = path.join(base_directory_name, export_filename)
            # if not path.exists(download_experiment_directory):
            #     error_msg, download_experiment_directory = create_directory(directory_download_base, str(experiment_id))

            # download_complete_filename = path.join(download_experiment_directory, export_filename)

            with ZipFile(export_complete_filename, 'w') as zip_file:
                for filename, directory in export.files_to_zip_list:
                    fdir, fname = path.split(filename)

                    zip_file.write(filename.encode('utf-8'), path.join(directory, fname))

            zip_file.close()

            # output_download_file = path.join("download", path.join(path.join(str(experiment_id), str(export_filename))))
            #
            # with open(export_complete_filename, 'rb') as f:
            #     data = f.read()
            #
            # with open(download_complete_filename, 'wb') as f:
            #     f.write(data)

            # experimento ultima versão
            # experiment = get_object_or_404(Experiment, pk=experiment_id)
            # experiment.download_url = "download/" + str(experiment_id) + "/" + export_filename
            # experiment.save(update_fields=["download_url"])
            #
            # update_export_instance(input_export_file, output_download_file, export_instance)

        # delete temporary directory: from base_directory and below
        # base_export_directory = path.join(
        #     settings.MEDIA_ROOT, path.join("temp", str(export_instance.id))
        # )

        export_instance_directory = settings.MEDIA_ROOT + '/'
        temp_directory = path.join(export_instance_directory, path.join(EXPORT_DIRECTORY, str(export_instance.id)))
        rmtree(temp_directory, ignore_errors=True)

        if template_name != "":
            return error_msg

    except OSError as e:
        print(e)
        error_msg = e
        # messages.error(request, error_msg)
        # return render(request, template_name)
        if template_name != "":
            return error_msg
