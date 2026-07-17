from django.urls import path
from . import views

urlpatterns = [
    path('', views.asistente_view, name='asistente'),
    path('api/', views.api_asistente, name='api_asistente'),
]