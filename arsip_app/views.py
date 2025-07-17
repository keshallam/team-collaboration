import os
import json
import calendar

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import capfirst

from .models import Dokumen
from .forms import DokumenForm

# ==========================
# == DASHBOARD DAN LOGIN ==
# ==========================
@login_required
def dashboard(request):
    match request.user.level:
        case 'admin': return redirect('admin_dashboard')
        case 'uploader': return redirect('uploader_dashboard')
        case 'viewer': return redirect('viewer_dashboard')
    return HttpResponseForbidden("Level pengguna tidak dikenali.")

@login_required
def admin_dashboard(request):
    if request.user.level != 'admin':
        return HttpResponseForbidden("Kamu bukan admin!")

    filters = {
        'unit': request.GET.get('unit'),
        'tahun': request.GET.get('tahun'),
        'bulan': request.GET.get('bulan'),
        'jenis': request.GET.get('jenis'),
        'diunggah_oleh__username': request.GET.get('pengunggah'),
    }

    dokumen_list = Dokumen.objects.all()
    for key, value in filters.items():
        if value:
            dokumen_list = dokumen_list.filter(**{key: value})

    query = request.GET.get('q')
    if query:
        dokumen_list = dokumen_list.filter(
            Q(nomor_berkas__icontains=query) |
            Q(unit__icontains=query) |
            Q(jenis__icontains=query) |
            Q(diunggah_oleh__username__icontains=query)
        )

    tahun_sekarang = timezone.now().year
    dokumen_per_bulan = dokumen_list.filter(tahun=tahun_sekarang).values('bulan').annotate(jumlah=Count('arsip_id'))

    bulan_labels = [capfirst(calendar.month_name[i]) for i in range(1, 13)]
    jumlah_per_bulan = {bulan: 0 for bulan in bulan_labels}
    for entry in dokumen_per_bulan:
        jumlah_per_bulan[entry['bulan']] = entry['jumlah']

    context = {
        'jumlah_per_unit': dokumen_list.values('unit').annotate(jumlah=Count('arsip_id')),
        'bulan_labels': json.dumps(bulan_labels),
        'bulan_data': json.dumps([jumlah_per_bulan[bulan] for bulan in bulan_labels]),
        'jumlah_per_bulan': jumlah_per_bulan,
        'jenis_labels': json.dumps([j['jenis'].replace('_', ' ').title() for j in dokumen_list.values('jenis').annotate(jumlah=Count('arsip_id'))]),
        'jenis_data': json.dumps([j['jumlah'] for j in dokumen_list.values('jenis').annotate(jumlah=Count('arsip_id'))]),
        'user': request.user,
        'dokumen_list': dokumen_list.order_by('-created_at'),

        'daftar_unit': Dokumen.objects.values_list('unit', flat=True).distinct(),
        'daftar_tahun': Dokumen.objects.values_list('tahun', flat=True).distinct(),
        'daftar_bulan': Dokumen.objects.values_list('bulan', flat=True).distinct(),
        'daftar_jenis': Dokumen.objects.values_list('jenis', flat=True).distinct(),
        'daftar_pengunggah': Dokumen.objects.exclude(diunggah_oleh=None).values_list('diunggah_oleh__username', flat=True).distinct(),

        **{f'{key}_dipilih': value for key, value in filters.items()},
        'pengunggah_terpilih': request.GET.get('pengunggah'),
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def uploader_dashboard(request):
    return render(request, 'dashboard/uploader_dashboard.html', {'user': request.user})

@login_required
def viewer_dashboard(request):
    return render(request, 'dashboard/viewer_dashboard.html', {'user': request.user})

@login_required
def after_login(request):
    return dashboard(request)

# =============================
# == DOKUMEN / ARSIP LOGIKA ==
# =============================
@login_required
def daftar_file(request):
    dokumen_list = Dokumen.objects.filter(unit=request.user.unit_kerja)

    for param in ['unit', 'tahun', 'bulan']:
        value = request.GET.get(param)
        if value:
            dokumen_list = dokumen_list.filter(**{param: value})

    context = {
        'dokumen_list': dokumen_list.order_by('-created_at'),
        'daftar_unit': dokumen_list.values_list('unit', flat=True).distinct(),
        'daftar_tahun': dokumen_list.values_list('tahun', flat=True).distinct(),
        'daftar_bulan': dokumen_list.values_list('bulan', flat=True).distinct(),
        'unit_dipilih': request.GET.get('unit'),
        'tahun_dipilih': request.GET.get('tahun'),
        'bulan_dipilih': request.GET.get('bulan'),
        'user': request.user,
    }
    return render(request, 'arsip_app/daftar_file.html', context)

@csrf_exempt
@login_required
def scanned_upload(request):
    if request.user.level not in ['admin', 'uploader']:
        return HttpResponseForbidden("Kamu tidak boleh mengunggah hasil scan.")

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        save_path = os.path.join(settings.MEDIA_ROOT, 'scanned', uploaded_file.name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        request.session['scanned_file'] = f'scanned/{uploaded_file.name}'
        return redirect('tambah_file')

    return HttpResponse('Hanya menerima POST dengan file.', status=400)

@login_required
def tambah_dokumen(request):
    if request.user.level not in ['admin', 'uploader']:
        return HttpResponseForbidden("Kamu tidak punya akses untuk menambahkan dokumen.")

    initial = {'unit': request.user.unit_kerja}
    scanned_file = request.session.pop('scanned_file', None)
    if scanned_file:
        initial['file_scan'] = scanned_file

    form = DokumenForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        dokumen = form.save(commit=False)
        if dokumen.unit != request.user.unit_kerja:
            return HttpResponse("Tidak boleh unggah dokumen untuk unit lain!", status=403)
        dokumen.diunggah_oleh = request.user
        dokumen.save()
        return redirect('daftar_file')

    return render(request, 'arsip_app/tambah_dokumen.html', {
        'form': form,
        'scanned_file': scanned_file,
    })

@login_required
def daftar_verifikasi(request):
    if request.user.level != 'admin':
        return HttpResponseForbidden("Hanya admin yang dapat melihat ini.")

    dokumen_list = Dokumen.objects.filter(unit=request.user.unit_kerja, status='belum verifikasi')
    return render(request, 'arsip_app/verifikasi_dokumen.html', {'dokumen_list': dokumen_list})

@require_POST
@login_required
def verifikasi_dokumen(request):
    if request.user.level != 'admin':
        return HttpResponseForbidden("Hanya admin yang boleh memverifikasi.")

    dokumen_ids = request.POST.getlist('dokumen_ids')
    dokumen_terverifikasi = []

    for dokumen_id in dokumen_ids:
        dokumen = get_object_or_404(Dokumen, pk=dokumen_id)
        if dokumen.unit == request.user.unit_kerja:
            dokumen.status = 'terverifikasi'
            dokumen.save()
            dokumen_terverifikasi.append(dokumen)

    dokumen_list = Dokumen.objects.filter(unit=request.user.unit_kerja, status='belum verifikasi')
    return render(request, 'arsip_app/verifikasi_dokumen.html', {
        'dokumen_list': dokumen_list,
        'berhasil_verifikasi': dokumen_terverifikasi,
    })

@login_required
def edit_dokumen(request, id):
    dokumen = get_object_or_404(Dokumen, pk=id)

    if request.user.level != 'admin' or dokumen.unit != request.user.unit_kerja:
        return HttpResponse('Tidak diizinkan.', status=403)

    form = DokumenForm(request.POST or None, request.FILES or None, instance=dokumen)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('daftar_file')

    return render(request, 'arsip_app/tambah_dokumen.html', {'form': form})

@require_POST
@login_required
def hapus_dokumen(request, id):
    dokumen = get_object_or_404(Dokumen, pk=id)
    if request.user.level != 'admin' or dokumen.unit != request.user.unit_kerja:
        return HttpResponse('Tidak diizinkan.', status=403)

    dokumen.delete()
    return redirect('daftar_file')

@login_required
def download_file(request, dokumen_id, tipe_file):
    dokumen = get_object_or_404(Dokumen, pk=dokumen_id)
    file_field = dokumen.file_scan if tipe_file == 'scan' else dokumen.file_upload if tipe_file == 'upload' else None

    if not file_field:
        raise Http404("File tidak ditemukan.")

    file_path = file_field.path
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    raise Http404("File tidak ditemukan.")
