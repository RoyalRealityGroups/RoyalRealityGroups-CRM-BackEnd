from drf_spectacular.extensions import OpenApiAuthenticationExtension

class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'Core.Core.authentication.Authentication.JWTAuthentication'  # path to your actual class
    name = 'Bearer'  # must match the name in SPECTACULAR_SETTINGS

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }