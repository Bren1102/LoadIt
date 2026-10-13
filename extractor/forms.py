from django import forms
from .models import OperacionAduanera

class OperacionAduaneraForm(forms.ModelForm):
    class Meta:
        model = OperacionAduanera
        fields = ['pais_destino', 'factura_proforma', 'instrucciones_embarque', 'etiquetas_producto']
        widgets = {
            'pais_destino': forms.Select(attrs={'class': 'form-select border-secondary-subtle py-2'}),
            'factura_proforma': forms.FileInput(attrs={'class': 'form-control border-secondary-subtle py-2', 'accept': '.pdf,.doc,.docx'}),
            'instrucciones_embarque': forms.FileInput(attrs={'class': 'form-control border-secondary-subtle py-2', 'accept': '.pdf,.doc,.docx'}),
            'etiquetas_producto': forms.FileInput(attrs={'class': 'form-control border-secondary-subtle py-2', 'accept': '.pdf,.doc,.docx'}),
        }