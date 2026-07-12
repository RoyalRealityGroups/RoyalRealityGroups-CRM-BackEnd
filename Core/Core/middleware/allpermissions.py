


class allPermissionsMiddleware(object):
    """
    Middleware which Add all User Permissions and user 
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        
        l = request.user.get_all_permissions()
        l_as_list = list(l) 

        # ADDED NEW VARIABLES
        request.allPermissions =  l_as_list
        request.allScreenPermissions =  list(map(lambda x: x.split(".")[-1], l_as_list)) 
        response = self.get_response(request)

        return response
    
    
