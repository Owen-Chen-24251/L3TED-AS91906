"""
URL configuration for as91906 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def force_admin_login(request):
    logout(request)
    return redirect('/admin/login/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-login/', force_admin_login, name='force_admin_login'),
    path('', include('AC_Library.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # Adds the media URL pattern to serve media files during development.