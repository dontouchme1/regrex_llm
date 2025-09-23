from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from transform.views import TransformAPI, DownloadAPI


def root(request):
    return JsonResponse({"message": "Rhombus AI backend is running", "endpoints": ["/admin/", "/api/transform", "/api/download"]})

urlpatterns = [
    path('', root, name='root'),
    path('admin/', admin.site.urls),
    path('api/transform', TransformAPI.as_view(), name='transform'),
    path('api/download', DownloadAPI.as_view(), name='download'),
]
