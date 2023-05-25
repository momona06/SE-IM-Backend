from django.http import JsonResponse

def template_request(code, info, **extra_data):
    return JsonResponse({
        "code": code,
        "info": info,
        **extra_data
    })


BAD_METHOD = template_request(-3, "Bad method")
