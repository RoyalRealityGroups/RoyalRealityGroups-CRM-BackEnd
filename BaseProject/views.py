
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django.urls import reverse
from urllib.parse import urlparse
from django.conf import settings

# Create your views here.
def index_view(request):

    # full_path = request.get_full_path()
    # full_path = "" if full_path == "/" else full_path
    baseurl = "https://" if request.is_secure() else "http://"
    baseurl += request.get_host() # + full_path

    # iobaseurl = "wss://" if request.is_secure() else "ws://"
    # iobaseurl += urlparse(baseurl).hostname

    return render(request, "index.html", {'baseurl': baseurl ,  'iobaseurl':settings.IO_SERVER_URL})



def privacy_view(request):

    baseurl = "https://" if request.is_secure() else "http://"
    baseurl += request.get_host()

    return render(request, "privacypolicy.html", {'baseurl': baseurl})


