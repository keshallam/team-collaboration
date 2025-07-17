from django import forms
from .models import Dokumen

class DokumenForm(forms.ModelForm):
    setuju = forms.BooleanField(
        required=True,
        label='Saya menyetujui bahwa data yang saya masukkan sudah benar.',
        error_messages={
            'required': 'Kamu harus menyetujui terlebih dahulu sebelum mengirim.'
        },
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Dokumen
        exclude = ['diunggah_oleh']


        widgets = {
            'nama_dokumen': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'tahun': forms.TextInput(attrs={
                'id': 'id_tahun',
                'class': 'form-control tahun-picker',
                'placeholder': 'Pilih Tahun',
                'autocomplete': 'off',
                'readonly': 'readonly'
            }),
            'bulan': forms.TextInput(attrs={
                'id': 'id_bulan',
                'class': 'form-control bulan-picker',
                'placeholder': 'Pilih Bulan',
                'autocomplete': 'off',
                'readonly': 'readonly'
            }),
            'nomor': forms.TextInput(attrs={'class': 'form-control'}),
            'rak': forms.TextInput(attrs={'class': 'form-control'}),
            'kardus': forms.TextInput(attrs={'class': 'form-control'}),
            'jenis_dokumen': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tanggal_upload': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }
