from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static  # TODO: for development only.
# See https://docs.djangoproject.com/en/1.11/howto/static-files/#serving-static-files-during-development
from django.contrib import admin
from experiments import views
from experiments import api_urls

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(api_urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # TODO: for development only.
# See https://docs.djangoproject.com/en/1.11/howto/static-files/#serving-static-files-during-development
