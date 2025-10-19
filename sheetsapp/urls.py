from django.urls import path
from .views import dados_view

urlpatterns = [
    path("dados/", dados_view, name="dados"),
]
