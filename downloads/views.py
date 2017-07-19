from django.shortcuts import render
from django.http import HttpResponse
from .models import Export


# Create your views here.
def create_export_instance(user):
    export_instance = Export(user=user)

    export_instance.save()

    return export_instance

def download_view(request):
    return HttpResponse("Download view")
    # description = ''
    # context = {
    #     description : "download",
    # }
    #
    # return render(request, context)