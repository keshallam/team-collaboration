from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Dokumen, CustomUser

# Konfigurasi admin untuk model Dokumen
@admin.register(Dokumen)
class DokumenAdmin(admin.ModelAdmin):
    list_display = ('nama_file', 'unit', 'tahun', 'bulan', 'jenis', 'status', 'created_at')
    list_filter = ('unit', 'tahun', 'jenis', 'status')
    search_fields = ('nama_file', 'nomor', 'rak', 'kardus')

# Konfigurasi admin untuk model CustomUser agar muncul unit_kerja & level
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'unit_kerja', 'level', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi Tambahan', {
            'fields': ('unit_kerja', 'level'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informasi Tambahan', {
            'fields': ('unit_kerja', 'level'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
