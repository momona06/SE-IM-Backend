from django.http import JsonResponse


def request_failed(code, info, status_code=400):
     return JsonResponse({
         "code": code,
         "info": info
     }, status=status_code)


def return_field(obj_dict, field_list):

    return {
        k: v for k, v in obj_dict.items()
        if k in field_list
    }


def template_request(code, info, **extra_data):
    return JsonResponse({
        "code": code,
        "info": info,
        **extra_data
    })



BAD_METHOD = template_request(-3, "Bad method")
