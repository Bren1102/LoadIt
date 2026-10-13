import os
import json
import docx
import fitz
import pdfplumber  # <-- Nueva librería para el Plan B de extracción profunda
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

PROMPTS_POR_PAIS = {
    'ARGENTINA': """
        Sos un asistente experto en aduanas de Argentina. Tu tarea es extraer información de la documentación adjunta.
        Vas a recibir textos mezclados (Factura, Instrucciones, Etiquetas). Tu trabajo es unificar la información y devolver estrictamente un objeto JSON válido con los siguientes campos:
        - nro_certificado: El número identificador del documento.
        - exportador_nombre: Nombre o razón social del exportador.
        - importador_nombre: Nombre o razón social del importador en Argentina.
        - mercaderia_detalle: Descripción técnica consolidada de la mercadería.
        - peso_bruto_kg: Peso bruto expresado numéricamente en kilogramos.
    """,
    'BRASIL': """
        Sos un asistente experto en aduanas de Brasil. Tu tarea es extraer información de la documentación adjunta.
        Vas a recibir textos mezclados. Unificá la información y devolvé estrictamente un objeto JSON válido:
        - nro_certificado: Número do certificado.
        - exportador_nombre: Nome do exportador.
        - importador_nombre: Nome do importador no Brasil.
        - mercaderia_detalle: Descrição da mercadoria / NCM.
        - peso_bruto_kg: Peso bruto total em quilogramas (apenas números).
    """,
    'URUGUAY': """
        Sos un asistente experto en aduanas de Uruguay (DNA). Unificá la información de los documentos y extraé:
        - nro_certificado: Número de certificado o trámite VUCE.
        - exportador_nombre: Razón social del exportador origen.
        - importador_nombre: Razón social del importador en Uruguay.
        - mercaderia_detalle: Detalle de los bienes o productos.
        - peso_bruto_kg: Peso bruto expresado en kilogramos.
    """,
    'CHINA': """
        Sos un asistente experto en aduanas de China (GACC). Procesá la documentación consolidada y extraé estrictamente un JSON con:
        - nro_certificado: Número de certificado.
        - exportador_nombre: Nombre del expedidor / consignor.
        - importador_nombre: Nombre del destinatario / consignee.
        - mercaderia_detalle: Nombre científico y comercial.
        - peso_bruto_kg: Kilos netos o totales de la carga.
        - contenedor_nro: Número de contenedor.
        - precinto_nro: Número de precinto.
        - planta_registro: Número de registro de la planta.
    """,
    'TAILANDIA': """
        Sos un asistente experto en aduanas de Tailandia. Procesá los documentos y extraé un JSON con:
        - nro_certificado: Código de certificado.
        - exportador_nombre: Nombre del expedidor.
        - importador_nombre: Nombre del destinatario.
        - mercaderia_detalle: Especie animal y piezas.
        - peso_bruto_kg: Kilos netos numéricos.
        - contenedor_nro: Contenedor(es) N°.
        - precinto_nro: Precinto(s) N°.
        - planta_registro: Número de Establecimiento Oficial.
    """,
    'UNION_EUROPEA': """
        Sos un asistente experto en aduanas de la Unión Europea. Procesá los documentos y extraé un JSON con:
        - nro_certificado: Referencia del certificado.
        - exportador_nombre: Expedidor/Exportador.
        - importador_nombre: Destinatario/Importador.
        - mercaderia_detalle: Descripción de la partida.
        - peso_bruto_kg: Peso bruto total o neto.
        - contenedor_nro: Número de recipiente.
        - precinto_nro: Número de precinto.
        - codigo_nc: Código NC.
        - planta_registro: Número de registro/autorización.
    """
}

def leer_archivo(ruta):
    """Extrae texto de PDFs y Word aplicando estrategia Fallback para escaneados."""
    extension = ruta.split('.')[-1].lower()
    texto = ""
    try:
        if extension == "pdf":
            # --- PLAN A: Lectura rápida nativa con PyMuPDF ---
            doc = fitz.open(ruta)
            for pagina in doc:
                texto += pagina.get_text() + "\n"
            
            # --- CRITERIO DE FALLBACK ---
            # Si el texto es sospechosamente corto (ej. menos de 50 caracteres), asumimos que es escaneado
            if len(texto.strip()) < 50:
                texto = "" # Limpiamos el intento vacío
                # --- PLAN B: Lectura profunda basada en tablas y formas con pdfplumber ---
                with pdfplumber.open(ruta) as pdf:
                    for pagina in pdf.pages:
                        texto_pagina = pagina.extract_text()
                        if texto_pagina:
                            texto += texto_pagina + "\n"
                
                # Si sigue vacío, le dejamos un log explícito para que la IA sepa que es una imagen pura
                if len(texto.strip()) < 10:
                    texto = f"[ADVERTENCIA DE SISTEMA: El archivo {os.path.basename(ruta)} parece ser una imagen pura o escaneo sin capa de texto nativa.]"
                    
        elif extension in ["doc", "docx"]:
            doc = docx.Document(ruta)
            for para in doc.paragraphs:
                texto += para.text + "\n"
                
        return texto
    except Exception as e:
        return f"ERROR_LECTURA: {str(e)}"

def pedir_a_gemini(texto_completo, pais_destino):
    """Motor de IA configurado para procesar texto consolidado."""
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        pais_key = str(pais_destino).upper().strip()
        prompt_instruccion = PROMPTS_POR_PAIS.get(pais_key, PROMPTS_POR_PAIS['ARGENTINA'])
        
        prompt_final = (
            f"{prompt_instruccion}\n\n"
            f"IMPORTANTE: Recibirás información de varios documentos (Factura, Instrucciones, Etiquetas). "
            f"Unifica los datos, prioriza los valores técnicos y sé tolerante si algún documento avisa que es escaneado.\n\n"
            f"Datos consolidados para procesar:\n{texto_completo}"
        )
        
        response = model.generate_content(
            prompt_final,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        return response.text.strip()
        
    except Exception as e:
        return json.dumps({"error": "Fallo en conexion con SDK", "detalle": str(e)})