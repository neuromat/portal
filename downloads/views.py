from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def download_view(request):
    return HttpResponse("Download view")
    # description = ''
    # context = {
    #     description : "download",
    # }
    #
    # return render(request, context)