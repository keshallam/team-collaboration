from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.after_login),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('verifikasi/', views.daftar_verifikasi, name='daftar_verifikasi'),
     path('verifikasi/submit/', views.verifikasi_dokumen, name='verifikasi_dokumen'),
     
    path('after-login/', views.after_login, name='after_login'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/uploader/', views.uploader_dashboard, name='uploader_dashboard'),
    path('dashboard/viewer/', views.viewer_dashboard, name='viewer_dashboard'),
    
    path('kelola/', views.daftar_file, name='daftar_file'),
    path('tambah/', views.tambah_dokumen, name='tambah_file'),
    path('edit/<int:id>/', views.edit_dokumen, name='edit_file'),
    path('hapus/<int:id>/', views.hapus_dokumen, name='hapus_file'),

    path('scan-upload/', views.scanned_upload, name='scanned_upload'),
    path('download/<int:dokumen_id>/<str:tipe_file>/', views.download_file, name='download_file'),
]
