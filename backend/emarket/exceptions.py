from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    response.data = {"error": {"code": getattr(exc, "default_code", "error"), "detail": response.data}}
    return response
