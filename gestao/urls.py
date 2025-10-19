# gestao/urls.py  (ou o urls.py do seu projeto)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("resultados/", include("resultados.urls")),  # <- importante
]
