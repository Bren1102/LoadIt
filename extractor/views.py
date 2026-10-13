import os
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from docxtpl import DocxTemplate

from .models import OperacionAduanera, DocumentoAdjunto
from .utils import leer_archivo, pedir_a_gemini

@login_required
def dashboard(request):
    formularios = OperacionAduanera.objects.filter(usuario=request.user).order_by('-fecha_carga')
    return render(request, 'extractor/dashboard.html', {'formularios': formularios})

@login_required
@csrf_exempt  # Habilitado para pruebas de Postman
def subir_formulario(request):
    if request.method == 'POST':
        pais_destino = request.POST.get('pais_destino')
        
        operacion = OperacionAduanera.objects.create(
            usuario=request.user,
            pais_destino=pais_destino
        )
        
        archivos_factura = request.FILES.getlist('factura_proforma')
        archivos_instrucciones = request.FILES.getlist('instrucciones_embarque')
        archivos_etiquetas = request.FILES.getlist('etiquetas_producto')
        
        for f in archivos_factura:
            DocumentoAdjunto.objects.create(operacion=operacion, archivo=f, tipo='FACTURA')
        for f in archivos_instrucciones:
            DocumentoAdjunto.objects.create(operacion=operacion, archivo=f, tipo='INSTRUCCIONES')
        for f in archivos_etiquetas:
            DocumentoAdjunto.objects.create(operacion=operacion, archivo=f, tipo='ETIQUETA')
            
        texto_consolidado = ""
        for adjunto in operacion.documentos.all():
            texto_extraido = leer_archivo(adjunto.archivo.path)
            texto_consolidado += f"--- ARCHIVO TIPO: {adjunto.tipo} ({adjunto.archivo.name}) ---\n{texto_extraido}\n\n"
            
        respuesta_ia = pedir_a_gemini(texto_consolidado, operacion.pais_destino)
        
        try:
            datos = json.loads(respuesta_ia)
            operacion.nro_certificado_referencia = datos.get('nro_certificado', 'S/N')
            operacion.exportador_nombre = datos.get('exportador_nombre', 'S/D')
            operacion.importador_nombre = datos.get('importador_nombre', 'S/D')
            operacion.detalle_mercaderia = datos.get('mercaderia_detalle', respuesta_ia)
        except Exception:
            operacion.detalle_mercaderia = respuesta_ia
            
        operacion.save()
        return redirect('detalle_formulario', pk=operacion.id)
        
    return render(request, 'extractor/subir.html')

@login_required
def detalle_formulario(request, pk):
    operacion = get_object_or_404(OperacionAduanera, id=pk, usuario=request.user)
    
    if request.method == 'POST':
        operacion.nro_certificado_referencia = request.POST.get('nro_certificado')
        operacion.exportador_nombre = request.POST.get('exportador_nombre')
        operacion.importador_nombre = request.POST.get('importador_nombre')
        operacion.detalle_mercaderia = request.POST.get('detalle_mercaderia')
        operacion.observaciones_hermano = request.POST.get('observaciones_hermano')
        operacion.save()
        return redirect('dashboard')
        
    return render(request, 'extractor/detalle.html', {'formulario': operacion})

@login_required
def eliminar_operacion(request, pk):
    operacion = get_object_or_404(OperacionAduanera, id=pk, usuario=request.user)
    if request.method == 'POST':
        operacion.delete()
    return redirect('dashboard')

@login_required
def exportar_documento(request, pk, formato):
    operacion = get_object_or_404(OperacionAduanera, id=pk, usuario=request.user)
    
    if formato.lower() == 'word':
        # MAPA COMPLETO DE PLANTILLAS DE EXPORTACIÓN PAYS / SENASA
        mapa_plantillas = {
            # --- KOSOVO, UNIÓN EUROPEA Y EUROPA EXTENDIDA ---
            'KOSOVO': 'KOSOVO_FISH_CRUST_HC.docx',
            'ALEMANIA': 'ALEMANIA_FISH_CRUST_HC.docx',
            'AUSTRIA': 'AUSTRIA_FISH_CRUST_HC.docx',
            'BELGICA': 'BELGICA_FISH_CRUST_HC.docx',
            'BULGARIA': 'BULGARIA_FISH_CRUST_HC.docx',
            'CHIPRE': 'CHIPRE_FISH_CRUST_HC.docx',
            'CROACIA': 'CROACIA_FISH_CRUST_HC.docx',
            'DINAMARCA': 'DINAMARCA_FISH_CRUST_HC.docx',
            'ESLOVAQUIA': 'ESLOVAQUIA_FISH_CRUST_HC.docx',
            'ESLOVENIA': 'ESLOVENIA_FISH_CRUST_HC.docx',
            'ESPAÑA': 'ESPAÑA_FISH_CRUST_HC.docx',
            'ESTONIA': 'ESTONIA_FISH_CRUST_HC.docx',
            'FINLANDIA': 'FINLANDIA_FISH_CRUST_HC.docx',
            'FRANCIA': 'FRANCIA_FISH_CRUST_HC.docx',
            'GRECIA': 'GRECIA_FISH_CRUST_HC.docx',
            'HUNGRIA': 'HUNGRIA_FISH_CRUST_HC.docx',
            'IRLANDA': 'IRLANDA_FISH_CRUST_HC.docx',
            'ISLANDIA': 'ISLANDIA_PESCADO_5210.docx',
            'ISLAS_FEROE': 'ISLAS_FEROE_FISH_CRUST_HC.docx',
            'ITALIA': 'ITALIA_FISH_CRUST_HC.docx',
            'LETONIA': 'LETONIA_FISH_CRUST_HC.docx',
            'LITUANIA': 'LITUANIA_FISH_CRUST_HC.docx',
            'MALTA': 'MALTA_FISH_CRUST_HC.docx',
            'NORUEGA': 'NORUEGA_FISH_CRUST_HC.docx',
            'PAISES_BAJOS': 'PAISES_BAJOS_FISH_CRUST_HC.docx',
            'POLONIA': 'POLONIA_FISH_CRUST_HC.docx',
            'PORTUGAL': 'PORTUGAL_FISH_CRUST_HC.docx',
            'REPUBLICA_CHECA': 'REPUBLICA_CHECA_FISH_CRUST_HC.docx',
            'RUMANIA': 'RUMANIA_FISH_CRUST_HC.docx',
            'SUECIA': 'SUECIA_FISH_CRUST_HC.docx',
            'SUIZA': 'SUIZA_FISH_CRUST_HC.docx',
            
            # --- COMBINACIONES MULTILINGÜES UE ---
            'ALEMAN_CHECO': 'ALEMAN_CHECO_FISH_CRUST_HC.docx',
            'ALEMAN_ESLOVACO': 'ALEMANIA_ESLOVACO_FISH_CRUST_HC.docx',
            'ALEMAN_FRANCES': 'ALEMAN_FRANCES_FISH_CRUST_HC.docx',
            'ALEMAN_HOLANDES': 'ALEMAN_HOLANDES_FISH_CRUST_HC.docx',
            'ALEMAN_POLACO': 'ALEMAN_POLACO_FISH_CRUST_HC.docx',
            'ESLOVENO_HUNGARO': 'ESLOVENIA_HUNGARO_FISH_CRUST_HC.docx',
            'FRANCES_HOLANDES': 'FRANCES_HOLANDES_FISH_CRUST_HC.docx',
            'INGLES_ESTONIO': 'INGLES_ESTONIO_FISH_CRUST_HC.docx',
            'INGLES_POLACO': 'INGLES_POLACO_FISH_CRUST_HC.docx',
            'INGLES_RUMANO': 'INGLES_RUMANO_FISH_CRUST_HC.docx',
            'NEERLANDES_ESLOVACO': 'NEERLANDES_ESLOVACO_FISH_CRUST_HC.docx',
            'NEERLANDES_RUMANO': 'NEERLANDES_RUMANO_FISH_CRUST_HC.docx',
            'ANEXO_PROVISORIO_UE': 'AP_7903_UNION_EUROPEA_FISH_CRUST_HC.docx',
            
            # --- DESTINOS AMÉRICA, ASIA, ÁFRICA Y OCEANÍA ---
            'ARGENTINA': 'ARGENTINA_SENASA.docx',
            'AUSTRALIA': 'AUSTRALIA_PESCADO_6805.docx',
            'BRASIL': 'BRASIL_MAPA.docx',
            'CAMERUN': 'CAMERUN_PESCADO_0597.docx',
            'CANADA': 'CANADA_PESCADO_0598.docx',
            'CHINA': 'CHINA_GACC.docx',
            'GRAN_BRETAÑA': 'GRAN_BRETAÑA_PESCA_8523.docx',
            'INDONESIA': 'INDONESIA_PESCA_7668.docx',
            'ISLA_REUNION': 'ISLA_REUNION_PESCA_8092.docx',
            'MALASIA': 'MALASIA_PESCADO_5189.docx',
            'MARRUECOS': 'MARRUECOS_PESCADO_3172.docx',
            'NIGERIA': 'NIGERIA_PESCADO_0635.docx',
            'PARAGUAY': 'PARAGUAY_PESCADO_0638.docx',
            'TAILANDIA': 'TAILANDIA_FISHERY.docx',
            'TURQUIA': 'TURQUIA_PESCADO_5196.docx',
            'URUGUAY': 'URUGUAY_VUCE.docx',
        }
        
        pais_key = str(operacion.pais_destino).upper().strip().replace(' ', '_')
        nombre_plantilla = mapa_plantillas.get(pais_key, 'ESPAÑA_FISH_CRUST_HC.docx')
        ruta_plantilla = os.path.join(settings.BASE_DIR, 'templates_word', nombre_plantilla)
        
        if not os.path.exists(ruta_plantilla):
            return HttpResponse(
                f"Plantilla no encontrada: asegurate de guardar '{nombre_plantilla}' dentro de la carpeta 'templates_word/'",
                status=404
            )
        
        doc = DocxTemplate(ruta_plantilla)
        contexto = {
            'nro_certificado': operacion.nro_certificado_referencia or 'S/N',
            'exportador_nombre': operacion.exportador_nombre or 'S/D',
            'importador_nombre': operacion.importador_nombre or 'S/D',
            'detalle_mercaderia': operacion.detalle_mercaderia or 'S/D',
            'pais_destino': operacion.get_pais_destino_display() if hasattr(operacion, 'get_pais_destino_display') else operacion.pais_destino,
            'fecha_carga': operacion.fecha_carga.strftime('%d/%m/%Y'),
            'observaciones': operacion.observaciones_hermano or '',
        }
        
        doc.render(contexto)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="Certificado_{operacion.pais_destino}_Op{operacion.id}.docx"'
        doc.save(response)
        return response
        
    elif formato.lower() == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Operacion_{operacion.id}_Oficial.pdf"'
        response.write(b"Generacion dinamica de PDF en desarrollo.")
        return response
        
    else:
        return redirect('detalle_formulario', pk=operacion.id)