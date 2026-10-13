import google.generativeai as genai


def pedir_a_gemini(texto_completo):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Este prompt es más agresivo para que no se salte nada
    prompt = f"""
    Actúa como un experto en trámites de aduana de SENASA. 
    Analiza el siguiente texto extraído de un documento (PDF o Word) y extrae CADA CASILLA numerada.
    
    Formato de salida esperado (JSON):
    {{
        "identificacion": {{
            "I.1_exportador": {{"nombre": "", "direccion": "", "pais": "", "codigo_iso": ""}},
            "I.2_referencia_certificado": "",
            "I.2a_referencia_sgico": ""
        }},
        "transporte": {{
            "I.15_medio_transporte": {{"tipo": "", "identificacion": ""}},
            "I.19_recipiente_precinto": {{"numero_recipiente": "", "numero_precinto": ""}}
        }},
        "mercaderia": {{
            "I.27_descripcion": {{
                "codigo_nc": "",
                "especie": "",
                "lote": "",
                "peso_neto": "",
                "fecha_produccion": ""
            }}
        }}
    }}

    Si el dato no figura en el texto, devolvé "No especificado".
    Texto del formulario:
    {texto_completo}
    """
    
    response = model.generate_content(prompt)
    return response.text