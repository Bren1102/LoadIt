from django.db import models
from django.contrib.auth.models import User

class OperacionAduanera(models.Model):
    PAISES_DESTINO = [
        ('ARGENTINA', 'Argentina'),
        ('CHINA', 'China'),
        ('UNION_EUROPEA', 'Unión Europea'),
        ('BRASIL', 'Brasil'),
        ('URUGUAY', 'Uruguay'),
        ('TAILANDIA', 'Tailandia'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    pais_destino = models.CharField(max_length=50, choices=PAISES_DESTINO)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    
    # Datos consolidados del formulario espejo
    nro_certificado_referencia = models.CharField(max_length=100, blank=True, null=True, default="S/N")
    exportador_nombre = models.CharField(max_length=255, blank=True, null=True, default="S/D")
    importador_nombre = models.CharField(max_length=255, blank=True, null=True, default="S/D")
    detalle_mercaderia = models.TextField(blank=True, null=True)
    observaciones_hermano = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Operación {self.id} - {self.pais_destino}"

class DocumentoAdjunto(models.Model):
    TIPO_DOC = [
        ('FACTURA', 'Factura Proforma'),
        ('INSTRUCCIONES', 'Instrucciones de Embarque'),
        ('ETIQUETA', 'Etiqueta de Producto'),
        ('OTRO', 'Otro Adjunto'),
    ]
    
    operacion = models.ForeignKey(OperacionAduanera, on_delete=models.CASCADE, related_name='documentos')
    archivo = models.FileField(upload_to='documentos/')
    tipo = models.CharField(max_length=20, choices=TIPO_DOC, default='OTRO')

    def __str__(self):
        return f"{self.tipo} - {self.archivo.name}"