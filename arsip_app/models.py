from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

# =============================
# Custom User Model
# =============================

class CustomUser(AbstractUser):
    UNIT_CHOICES = [
        ('UPP', 'UPP'), ('USD', 'USD'), ('UPA', 'UPA'), ('UKS', 'UKS'),
        ('UDP', 'UDP'), ('UPS', 'UPS'), ('UPI', 'UPI'), ('UAP', 'UAP'),
    ]

    LEVEL_CHOICES = [
        ('viewer', 'Viewer'),
        ('uploader', 'Uploader'),
        ('admin', 'Admin'),
    ]

    unit_kerja = models.CharField("Unit Kerja", max_length=3, choices=UNIT_CHOICES)
    level = models.CharField("Level Akses", max_length=10, choices=LEVEL_CHOICES)

    def __str__(self):
        return f"{self.username} | {self.unit_kerja} | {self.level}"


# =============================
# Dokumen Arsip Model
# =============================

class Dokumen(models.Model):
    JENIS_CHOICES = [
        ('surat_masuk', 'Surat Masuk'),
        ('surat_keluar', 'Surat Keluar'),
        ('surat_tugas', 'Surat Tugas'),
        ('data_pengawas_pengurus_dan_pegawai', 'Data Pengawas, Pengurus, dan Pegawai'),
        ('surat_ijin_/_cuti', 'Surat Ijin / Cuti'),
        ('call_memo', 'Call Memo'),
        ('nota_interm', 'Nota Interm'),
        ('pinjaman_anggota', 'Pinjaman Anggota'),
        ('nota_dinas', 'Nota Dinas'),
        ('jurnal_&_lampiran', 'Jurnal & Lampiran'),
        ('perjanjian_kerjasama', 'Perjanjian Kerjasama'),
        ('laporan_keuangan_koperasi_swadharma', 'Laporan Keuangan Koperasi Swadharma'),
        ('laporan_keuangan_perusahaan_anak', 'Laporan Keuangan Perusahaan Anak'),
        ('notulen_rapat', 'Notulen Rapat'),
        ('dokumen_RAT', 'Dokumen RAT'),
        ('bpp', 'BPP (Buku Peraturan Perusahaan)'),
        ('laporan_pajak', 'Laporan Pajak'),
        ('sk_pengurus', 'SK Pengurus'),
    ]

    BULAN_CHOICES = [
        ('Januari', 'Januari'), ('Februari', 'Februari'), ('Maret', 'Maret'),
        ('April', 'April'), ('Mei', 'Mei'), ('Juni', 'Juni'), ('Juli', 'Juli'),
        ('Agustus', 'Agustus'), ('September', 'September'), ('Oktober', 'Oktober'),
        ('November', 'November'), ('Desember', 'Desember'),
    ]

    TAHUN_CHOICES = [(r, r) for r in range(2000, timezone.now().year + 1)]

    STATUS_CHOICES = [
        ('belum verifikasi', 'Belum Verifikasi'),
        ('sudah verifikasi', 'Sudah Verifikasi'),
    ]

    # ==== Informasi Utama ====
    arsip_id       = models.AutoField("ID Arsip", primary_key=True)
    nama_file      = models.CharField("Nama File", max_length=255)
    unit           = models.CharField("Unit", max_length=3, choices=CustomUser.UNIT_CHOICES)
    jenis          = models.CharField("Jenis Dokumen", max_length=50, choices=JENIS_CHOICES)
    nomor_berkas   = models.CharField("Nomor Berkas", max_length=100, blank=True)
    nomor          = models.CharField("Nomor", max_length=50)
    tahun          = models.IntegerField("Tahun", choices=TAHUN_CHOICES)
    bulan          = models.CharField("Bulan", max_length=10, choices=BULAN_CHOICES)
    rak            = models.CharField("Rak", max_length=50)
    kardus         = models.CharField("Kardus", max_length=50)

    # ==== File ====
    file_scan      = models.FileField("File Scan", upload_to='scan/', blank=True, null=True)
    file_upload    = models.FileField("File Upload", upload_to='upload/', blank=True, null=True)

    # ==== Metadata ====
    status         = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default='belum verifikasi')
    created_at     = models.DateTimeField("Tanggal & Waktu Upload", auto_now_add=True)
    tanggal_upload = models.DateField("Tanggal Upload", auto_now_add=True)
    waktu_upload   = models.TimeField("Waktu Upload", auto_now_add=True)

    # ==== Relasi ====
    diunggah_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Diunggah Oleh"
    )

    def __str__(self):
        return f"{self.unit} | {self.nama_file} | {self.tahun}"
