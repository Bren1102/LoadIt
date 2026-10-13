from django.contrib import admin
from django.urls import path, include  # <-- Asegurá el 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('extractor.urls')),  # Las urls de tu app
    path('accounts/', include('django.contrib.auth.urls')),  
]