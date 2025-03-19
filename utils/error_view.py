from django.http import JsonResponse


def handler404(request,exception):
    massage = ('path not found')
    response = JsonResponse(data={'error':massage})
    response.status_code=404
    return response

def handler500(request):
    massage = ('internal server error')
    response = JsonResponse(data={'error':massage})
    response.status_code=500
    return response