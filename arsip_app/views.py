import os
import json
import calendar
from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import capfirst
from django.contrib import messages 
from .models import Dokumen
from .forms import DokumenForm
from django import forms

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

    # === Ambil parameter filter dari request ===
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

    # === Pencarian ===
    query = request.GET.get('q')
    if query:
        dokumen_list = dokumen_list.filter(
            Q(nomor_berkas__icontains=query) |
            Q(unit__icontains=query) |
            Q(jenis__icontains=query) |
            Q(diunggah_oleh__username__icontains=query)
        )

    # === STATISTIK UTAMA ===
    # 1. Total dokumen (SEMUA UNIT - tanpa filter)
    total_dokumen_all = Dokumen.objects.count()

    # 2. Total dokumen pada hasil filter/pencarian (sinkron dengan tabel/pagination)
    total_dokumen = dokumen_list.count()

    # 3. Total dokumen untuk unit user login (DOKUMEN PER UNIT)
    user_unit = getattr(request.user, 'unit', None) or getattr(request.user, 'unit_kerja', None)
    dokumen_unit = Dokumen.objects.filter(unit=user_unit).count() if user_unit else 0

    # 4. Dokumen baru hari ini (di semua dokumen/filter)
    today = timezone.localdate()
    dokumen_baru = dokumen_list.filter(created_at__date=today).count()

    # === Grafik tren dokumen baru per bulan di tahun berjalan ===
    tahun_ini = timezone.now().year
    bulan_labels = [capfirst(calendar.month_name[i]) for i in range(1, 13)]
    data_baru = []
    for i in range(1, 13):
        jumlah = dokumen_list.filter(created_at__year=tahun_ini, created_at__month=i).count()
        data_baru.append(jumlah)

    # === Pie chart distribusi jenis dokumen ===
    jenis_stat = dokumen_list.values('jenis').annotate(jumlah=Count('arsip_id'))
    jenis_labels = [j['jenis'].replace('_', ' ').title() for j in jenis_stat]
    jenis_data = [j['jumlah'] for j in jenis_stat]
    donut_colors = ["#3b82f6", "#8b5cf6", "#10b981", "#fbbf24", "#fb7185", "#6366f1", "#f59e42", "#14b8a6"][:len(jenis_labels)]

    # === Statistik Dokumen per Unit (untuk tabel mini bawah) ===
    jumlah_per_unit = dokumen_list.values('unit').annotate(jumlah=Count('arsip_id'))

    # === Semua data untuk filter dropdown ===
    daftar_unit = Dokumen.objects.values_list('unit', flat=True).distinct()
    daftar_tahun = Dokumen.objects.values_list('tahun', flat=True).distinct()
    daftar_bulan = Dokumen.objects.values_list('bulan', flat=True).distinct()
    daftar_jenis = Dokumen.objects.values_list('jenis', flat=True).distinct()
    daftar_rak = Dokumen.objects.values_list('rak', flat=True).distinct()
    daftar_kardus = Dokumen.objects.values_list('kardus', flat=True).distinct()
    daftar_pengunggah = Dokumen.objects.exclude(diunggah_oleh=None)\
        .values_list('diunggah_oleh__username', flat=True).distinct()

    # === Aktivitas terbaru (opsional, dummy/manual) ===
    aktivitas_terbaru = [
        {"type": "new", "title": "Dokumen baru ditambahkan", "desc": "Laporan Tahunan 2023 telah diunggah oleh Admin • 2 jam yang lalu"},
    ]

    # === PAGINATION ===
    page = request.GET.get('page', 1)
    paginator = Paginator(dokumen_list.order_by('-created_at'), 10)
    try:
        dokumen_page = paginator.page(page)
    except PageNotAnInteger:
        dokumen_page = paginator.page(1)
    except EmptyPage:
        dokumen_page = paginator.page(paginator.num_pages)

    doc_index_start = (dokumen_page.number - 1) * paginator.per_page + 1

    context = {
        'user': request.user,
        'dokumen_page': dokumen_page,
        'paginator': paginator,
        'doc_index_start': doc_index_start,

        # Statistik
        'total_dokumen': total_dokumen,            # Dokumen pada tabel aktif
        'total_dokumen_all': total_dokumen_all,    # Semua dokumen (tanpa filter)
        'dokumen_unit': dokumen_unit,
        'dokumen_baru': dokumen_baru,
        'jumlah_per_unit': jumlah_per_unit,

        # Grafik
        'bulan_labels': json.dumps(bulan_labels),
        'data_baru': json.dumps(data_baru),
        'donut_labels': json.dumps(jenis_labels),
        'donut_data': json.dumps(jenis_data),
        'donut_colors': json.dumps(donut_colors),

        # Aktivitas terbaru
        'aktivitas_terbaru': aktivitas_terbaru,

        # Filter dropdown
        'daftar_unit': daftar_unit,
        'daftar_tahun': daftar_tahun,
        'daftar_bulan': daftar_bulan,
        'daftar_jenis': daftar_jenis,
        'daftar_rak': daftar_rak,
        'daftar_kardus': daftar_kardus,
        'daftar_pengunggah': daftar_pengunggah,

        # Filter aktif
        **{f'{key}_dipilih': value for key, value in filters.items()},
        'pengunggah_terpilih': request.GET.get('pengunggah'),
        'query': query,
        'request': request,  # biar bisa akses GET di template
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
    step = int(request.POST.get('step', request.GET.get('step', 1)))
    step = max(1, min(step, 5))

    step_fields = {
        1: ['nama_file', 'jenis', 'unit', 'nomor_berkas', 'nomor', 'nomor_surat'],
        2: ['tahun', 'bulan'],
        3: ['rak', 'kardus'],
        4: ['file_scan', 'file_upload'],
        5: ['status', 'setuju'],
    }

    def get_step_form(step, step_fields):
        class StepForm(forms.ModelForm):
            class Meta:
                model = Dokumen
                if step < 5:
                    fields = step_fields[step]
                else:
                    # Di step 5, FINAL FORM, pakai semua fields dari semua step!
                    fields = (
                        step_fields[1] + step_fields[2] + step_fields[3] +
                        step_fields[4] + step_fields[5]
                    )
            if step == 5:
                setuju = forms.BooleanField(
                    required=True,
                    label='Saya menyetujui bahwa data yang saya masukkan sudah benar.',
                    error_messages={
                        'required': 'Kamu harus menyetujui terlebih dahulu sebelum mengirim.'
                    },
                    widget=forms.CheckboxInput(attrs={'class': 'wizard-checkbox'})
                )
        return StepForm

    if 'wizard_data' not in request.session:
        request.session['wizard_data'] = {}
    wizard_data = request.session['wizard_data']

    initial = wizard_data.copy()
    StepForm = get_step_form(step, step_fields)
    form = StepForm(request.POST or None, request.FILES or None, initial=initial)

    print("STEP:", step)
    print("FIELDS:", list(form.fields.keys()))

    if request.method == 'POST':
        if 'prev_step' in request.POST:
            prev = step - 1
            return redirect(f"{request.path}?step={prev}")
        elif form.is_valid():
            # Simpan data ke wizard_data (tanpa file upload!)
            for field in step_fields[step]:
                if field not in ['file_scan', 'file_upload']:
                    wizard_data[field] = form.cleaned_data.get(field)
            request.session['wizard_data'] = wizard_data

            if step < 5:
                return redirect(f"{request.path}?step={step+1}")
            else:
                # FINAL SUBMIT: Gabung data session + ambil file dari request.FILES
                final_data = wizard_data.copy()
                final_data['status'] = form.cleaned_data.get('status')
                final_data['setuju'] = form.cleaned_data.get('setuju')

                # File upload ambil dari request.FILES, bukan dari session
                final_files = {}
                for file_field in ['file_scan', 'file_upload']:
                    if file_field in request.FILES:
                        final_files[file_field] = request.FILES[file_field]

                # DEBUG: print semua data sebelum simpan
                print("SESSION WIZARD DATA:", wizard_data)
                print("FINAL DATA:", final_data)
                print("FILES:", final_files)

                final_form = get_step_form(5, step_fields)(final_data, final_files)
                if final_form.is_valid():
                    dokumen = final_form.save(commit=False)
                    dokumen.diunggah_oleh = request.user
                    dokumen.save()
                    request.session.pop('wizard_data', None)
                    messages.success(request, "Dokumen berhasil diupload!")
                    return dashboard(request)  # BARIS INI YANG DIUBAH
                else:
                    print("FORM ERROR:", final_form.errors)
                    form = final_form

    return render(request, 'arsip_app/tambah_dokumen.html', {
        'form': form,
        'step': step,
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
    messages.success(request, "Dokumen berhasil dihapus!")
    return redirect('all_documents')

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