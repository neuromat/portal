from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from .models import Export
from os import path
from zipfile import ZipFile
from shutil import rmtree

from .export import create_directory, ExportExecution
from .input_export import build_complete_export_structure

JSON_FILENAME = "json_export.json"
JSON_EXPERIMENT_FILENAME = "json_experiment_export.json"
EXPORT_DIRECTORY = "download"
EXPORT_FILENAME = "download.zip"
EXPORT_EXPERIMENT_FILENAME = "download_experiment.zip"


# Create your views here.
def create_export_instance(user):
    export_instance = Export(user=user)

    export_instance.save()

    return export_instance


def download_view(request, experiment_id):

    if request.method == "POST":
        export_instance = create_export_instance(request.user)
        input_export_file = path.join(EXPORT_DIRECTORY,
                                      path.join(str(request.user.id),
                                                path.join(str(export_instance.id), str(JSON_FILENAME))))
        input_filename = path.join(settings.MEDIA_ROOT, input_export_file)

        create_directory(settings.MEDIA_ROOT, path.split(input_export_file)[0])

        build_complete_export_structure(experiment_id, input_filename)

        complete_filename = export_create(request, export_instance.id, input_filename, experiment_id)

        if complete_filename:

            messages.success(request, "Export was finished correctly")

            print("antes do fim: httpResponse")

            zip_file = open(complete_filename, 'rb')
            response = HttpResponse(zip_file, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="export.zip"'
            response['Content-Length'] = path.getsize(complete_filename)
            return response
        else:
            messages.error(request, "Export data was not generated.")
            redirect_url = reverse("experiment-detail", args=(experiment_id,))
            return HttpResponseRedirect(redirect_url)


def get_export_instance(user, export_id):
    export_instance = Export.objects.get(user=user, id=export_id)

    return export_instance


def update_export_instance(input_file, output_export, export_instance):
    export_instance.input_file = input_file
    export_instance.output_export = output_export
    export_instance.save()


def export_create(request, export_id, input_filename, experiment_id, template_name="experiments/detail.html"):
    try:

        export_instance = get_export_instance(request.user, export_id)
        export = ExportExecution(export_instance.user.id, export_instance.id)

        # set path of the directory base: ex. /Users/.../portal/media/download/user.id
        base_directory, path_to_create = path.split(export.get_directory_base())
        # create directory base ex. /Users/.../portal/media/download/user.id/path_create
        error_msg, base_directory_name = create_directory(base_directory, path_to_create)
        if error_msg != "":
            messages.error(request, error_msg)
            return render(request, template_name)
        # ex. /Users/.../portal/media/download/user.id/export_instance.id/json_export.json
        input_export_file = path.join("export", path.join(str(request.user.id),
                                                          path.join(str(export_instance.id), str(input_filename))))

        # language_code = request.LANGUAGE_CODE
        # prepare data to be processed
        input_data = export.read_configuration_data(input_filename)

        if not export.is_input_data_consistent() or not input_data:
            messages.error(request, "Inconsistent data read from json file")
            return render(request, template_name)

        # create directory base for export: /EXPERIMENT_DOWNLOAD
        error_msg = export.create_export_directory()

        if error_msg != "":
            messages.error(request, error_msg)
            return render(request, template_name)

        # load information of the data collection per participant in a dictionnary
        error_msg = export.include_data_from_group(experiment_id)
        if error_msg != "":
            messages.error(request, error_msg)
            return render(request, template_name)

        # Create arquivos para exportação
        # create files protocolo experimental and diagnosis/participant csv file for each group
        error_msg = export.process_experiment_data(experiment_id)

        if error_msg != "":
            messages.error(request, error_msg)
            return render(request, template_name)
        # process the data per participant
        error_msg = export.download_data_per_participant()

        if error_msg != "":
            messages.error(request, error_msg)
            return render(request, template_name)

        # create zip file and include files
        export_complete_filename = ""
        if export.files_to_zip_list:
            export_filename = export.get_input_data("export_filename")  # 'download.zip'

            export_complete_filename = path.join(base_directory_name, export_filename)

            with ZipFile(export_complete_filename, 'w') as zip_file:
                for filename, directory in export.files_to_zip_list:
                    fdir, fname = path.split(filename)

                    zip_file.write(filename.encode('utf-8'), path.join(directory, fname))

            zip_file.close()

            output_export_file = path.join("download", path.join(str(export_instance.user.id), path.join(str(
                export_instance.id), str(export_filename))))

            update_export_instance(input_export_file, output_export_file, export_instance)

            print("finalizado corretamente")

        # delete temporary directory: from base_directory and below
        base_export_directory = export.get_export_directory()
        rmtree(base_export_directory)

        # messages.success(request, "Export was finished correctly")
        print("finalizado corretamente 2")

        return export_complete_filename

    except OSError as e:
        print(e)
        error_msg = e
        messages.error(request, error_msg)
        return render(request, template_name)
