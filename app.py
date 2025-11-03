from flask import Flask, request, jsonify
import os
from google import genai 
import logging

# Configurar logging para ver errores en los logs de Render
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# OBTENER la clave de API de la variable de entorno de Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logging.error("FATAL: La variable de entorno GEMINI_API_KEY no está configurada en Render.")
    client = None
else:
    client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/webhook', methods=['POST'])
def webhook():
    # 1. Verificar si el cliente de Gemini se inicializó
    if client is None:
        logging.warning("El cliente de Gemini no está inicializado. Error de configuración de API Key.")
        # Usamos el formato estricto de Dialogflow para el error
        return jsonify({
            "fulfillmentMessages": [{
                "text": { "text": ["Lo siento, el servicio de IA no está configurado correctamente (Error de API Key)."] }
            }]
        }), 500

    try:
        req = request.get_json(silent=True, force=True) # Uso silent=True, force=True para mayor robustez
        
        # Extraer el texto de la consulta del usuario
        # Dialogflow usa 'queryText' para el texto literal
        user_message = req.get('queryResult', {}).get('queryText', '')
        
        if not user_message:
            logging.warning("Mensaje de usuario vacío recibido.")
            return jsonify({
                 "fulfillmentMessages": [{
                    "text": { "text": ["Por favor, dime qué quieres preguntar sobre IA."] }
                }]
            })

        # Prompt base
        system_prompt = (
            "Eres un chatbot experto en Inteligencia Artificial Generativa. "
            "Explicas conceptos de forma clara, profesional y amigable. "
            "Responde en español."
        )

        # 3. Llamada a la API de Google Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7 
            }
        )

        answer = response.text
        logging.info("Respuesta de Gemini generada con éxito.")

        # 4. Devolver respuesta a Dialogflow (¡FORMATO ESTRICTO!)
        # Usamos fulfillmentMessages con una lista de textos. 
        # Este formato es el más compatible y evita el "Not available".
        return jsonify({
            "fulfillmentMessages": [{
                "text": { "text": [answer] }
            }]
        })

    except Exception as e:
        logging.error(f"Error inesperado durante la ejecución: {e}", exc_info=True)
        # Devolver un error amigable a Dialogflow si falla la llamada
        return jsonify({
            "fulfillmentMessages": [{
                "text": { "text": [f"Lo siento, ocurrió un error interno al contactar a la IA: {e}"] }
            }]
        }), 500 # Devolvemos un código de error interno 500


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
