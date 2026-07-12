from rest_framework.negotiation import BaseContentNegotiation

class ContentNegotiation(BaseContentNegotiation):

    def select_renderer(self, request, renderers, format_suffix):
        """
        Select the first renderer in the `.renderer_classes` list.
        """
        return (renderers[0], renderers[0].media_type)