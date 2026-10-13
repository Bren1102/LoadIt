import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from .models import OperacionAduanera, DocumentoAdjunto

class LoadItQASuite(TestCase):

    def setUp(self):
        """
        [BANCO DE PRUEBAS] Se ejecuta antes de CADA test.
        Preparamos un usuario de prueba en la memoria RAM.
        """
        self.client = Client()
        self.username = "ale_qa_lead"
        self.password = "Testing2026!"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    # ------------------------------------------------------------------
    # TEST 1: Verificar Base de Datos y Creación de Operaciones
    # ------------------------------------------------------------------
    def test_01_crear_operacion_base(self):
        """QA-01: Verifica que se guarde una operación de exportación a China."""
        operacion = OperacionAduanera.objects.create(
            usuario=self.user,
            pais_destino="CHINA",
            nro_certificado_referencia="CH-2026-001",
            exportador_nombre="Pesquera Argentina S.A.",
            importador_nombre="Shanghai Trading Co.",
            detalle_mercaderia="Calamar Illex Argentinus"
        )
        
        # Aserciones (Asserts): Comprobar que los datos son correctos
        self.assertEqual(operacion.pais_destino, "CHINA")
        self.assertEqual(operacion.nro_certificado_referencia, "CH-2026-001")
        self.assertEqual(operacion.documentos.count(), 0) # Al principio no tiene archivos

    # ------------------------------------------------------------------
    # TEST 2: Relaciones Multi-Archivo (Adjuntos)
    # ------------------------------------------------------------------
    def test_02_vincular_multiples_documentos(self):
        """QA-02: Verifica que una misma operación tenga Factura, Instrucciones y Etiquetas."""
        operacion = OperacionAduanera.objects.create(usuario=self.user, pais_destino="ESPAÑA")
        
        doc1 = DocumentoAdjunto.objects.create(operacion=operacion, tipo="FACTURA", archivo="factura_test.pdf")
        doc2 = DocumentoAdjunto.objects.create(operacion=operacion, tipo="INSTRUCCIONES", archivo="instrucciones_test.pdf")
        doc3 = DocumentoAdjunto.objects.create(operacion=operacion, tipo="ETIQUETA", archivo="etiqueta_test.pdf")
        
        self.assertEqual(operacion.documentos.count(), 3)
        self.assertEqual(doc1.tipo, "FACTURA")

    # ------------------------------------------------------------------
    # TEST 3: Seguridad y Accesos (Middlewares / Auth)
    # ------------------------------------------------------------------
    def test_03_seguridad_usuario_no_autenticado(self):
        """QA-03: Un extraño intenta entrar al Dashboard sin loguearse. Debe rebotar."""
        url = reverse('dashboard')
        response = self.client.get(url)
        
        # Status 302 significa REDIRECCIÓN al formulario de Login
        self.assertEqual(response.status_code, 302)

    # ------------------------------------------------------------------
    # TEST 4: Login y Navegación
    # ------------------------------------------------------------------
    def test_04_acceso_dashboard_autenticado(self):
        """QA-04: el usuario se loguea y accede exitosamente al Dashboard."""
        self.client.login(username=self.username, password=self.password)
        url = reverse('dashboard')
        response = self.client.get(url)
        
        # Status 200 significa OK
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # TEST 5: Control de Plantillas Word (Exportación)
    # ------------------------------------------------------------------
    def test_05_error_si_plantilla_no_existe(self):
        """QA-05: Si pedimos exportar a un país sin plantilla guardada, debe dar error 404."""
        self.client.login(username=self.username, password=self.password)
        
        # Creamos una operación con un país raro que no esté en la carpeta
        operacion = OperacionAduanera.objects.create(
            usuario=self.user, 
            pais_destino="PAIS_INEXISTENTE_TEST"
        )
        
        url = reverse('exportar_documento', kwargs={'pk': operacion.id, 'formato': 'word'})
        response = self.client.get(url)
        
        # Al no estar la plantilla física en disco, el sistema debe tirar un 404 manejado
        self.assertEqual(response.status_code, 404)