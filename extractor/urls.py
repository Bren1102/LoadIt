from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('subir/', views.subir_formulario, name='subir_formulario'),
    path('detalle/<int:pk>/', views.detalle_formulario, name='detalle_formulario'),
    path('detalle/<int:pk>/eliminar/', views.eliminar_operacion, name='eliminar_operacion'),
    path('detalle/<int:pk>/exportar/<str:formato>/', views.exportar_documento, name='exportar_documento'),
]