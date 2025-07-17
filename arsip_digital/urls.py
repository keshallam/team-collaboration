from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView  # untuk uji coba

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('arsip_app.urls')),  # include hanya di sini
]

# Untuk file media (upload/scan)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
