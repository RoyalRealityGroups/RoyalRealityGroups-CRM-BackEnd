
from Core.System.models import Error

class ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 500:
            current_url = request.path_info
            content = response.content
            code = response.status_code
            # request.query_params
            try:
                Error.objects.create(error_url = current_url, requestbody = "GET: {} BODY: {} POST: {}".format(request.GET.dict(), request.body.decode('utf-8'),request.POST.dict()), responsecontent = content, errorcode = code  ) # other data you want to store here
            except (UnicodeDecodeError, AttributeError) as e:
                # If body can't be decoded, log without it
                Error.objects.create(error_url = current_url, requestbody = "GET: {} POST: {}".format(request.GET.dict(),request.POST.dict()), responsecontent = content, errorcode = code  ) # other data you want to store here
            except Exception as e:
                # Log the error to prevent error middleware from failing
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create error log: {e}")

        return response