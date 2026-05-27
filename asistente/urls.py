from django.urls import path
from . import views

urlpatterns = [
    path('asistente/', views.asistente_view, name='asistente'),
    path('asistente/api/', views.api_asistente, name='api_asistente'),
]