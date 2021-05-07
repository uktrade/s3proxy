from authbroker_client import urls as authbroker_client_urls
from django.urls import include, path

from file_proxy.views import file_proxy

urlpatterns = [
    # URLs for Staff SSO Auth broker
    path("auth/", include(authbroker_client_urls)),
    path("<path:s3_path>", file_proxy, name="file_proxy"),
]
