from django import forms
from .models import Dokumen

class DokumenForm(forms.ModelForm):
    setuju = forms.BooleanField(
        required=True,
        label='Saya menyetujui bahwa data yang saya masukkan sudah benar.',
        error_messages={
            'required': 'Kamu harus menyetujui terlebih dahulu sebelum mengirim.'
        },
        widget=forms.CheckboxInput(attrs={'class': 'wizard-checkbox'})
    )

    class Meta:
        model = Dokumen
        exclude = ['diunggah_oleh']
        widgets = {
            'nama_file': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'tahun': forms.Select(attrs={'class': 'form-control'}),      
            'bulan': forms.Select(attrs={'class': 'form-control'}),      
            'nomor': forms.TextInput(attrs={'class': 'form-control'}),
            'rak': forms.TextInput(attrs={'class': 'form-control'}),
            'kardus': forms.TextInput(attrs={'class': 'form-control'}),
            'jenis': forms.Select(attrs={'class': 'form-control'}),      
            'nomor_berkas': forms.TextInput(attrs={'class': 'form-control'}),
            'nomor_surat': forms.TextInput(attrs={'class': 'form-control'}),
            'file_scan': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'file_upload': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tanggal_upload': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }