from django.http import HttpResponse


def experiment(request):
    return HttpResponse(content_type='application/json')
