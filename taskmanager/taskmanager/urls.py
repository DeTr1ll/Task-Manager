"""
URL configuration for taskmanager project.

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
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import get_language_from_request, get_supported_language_variant
from django.conf import settings
from django.views.i18n import set_language
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from tasks import views


def root_redirect(request):
    lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
    try:
        lang = get_supported_language_variant(lang)
    except (LookupError, TypeError):
        lang = get_language_from_request(request, check_path=False)

    return HttpResponseRedirect(f'/{lang}/' if lang else '/en/')

urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    path('api/send-daily/', views.trigger_deadlines, name='trigger_deadlines'),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('i18n/setlang/', set_language, name='set_language'),
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', include('tasks.urls')),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tasks/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
)
