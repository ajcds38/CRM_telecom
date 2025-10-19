# resultados/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("dados/", views.resultados_dados, name="resultados_dados"),
]
