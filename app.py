from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from google import genai
import logging

# Configuración de Logging para ver más detalles
logging.basicConfig(level=logging.INFO)

# 1. Cargar la API Key y configurar Flask
load_dotenv()
app = Flask(__name__)

# Inicializar el cliente con la clave de Gemini
# Nota: La clave se carga automáticamente desde las variables de entorno si se llama a load_dotenv()
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    if not client:
        logging.error("GEMINI_API_KEY no se pudo inicializar. Verifica tu archivo .env.")
except Exception as e:
    logging.error(f"Error al inicializar el cliente Gemini: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    logging.info("Webhook recibido.")
    
    # 2. Extraer mensaje del usuario desde Dialogflow de forma segura
    req = request.get_json(silent=True, force=True)
    
    # Intenta obtener el queryText desde la estructura correcta de Dialogflow ES
    try:
        query_result = req.get('queryResult', {})
        user_message = query_result.get('queryText', '')
        
        # También verificamos la respuesta del intent de fallback para mayor robustez
        if not user_message:
            logging.error("No se pudo extraer queryText. Verificando alternativas...")
            # En algunos casos, Dialogflow envía el texto en la entrada de la sesión
            user_message = req.get('originalDetectIntentRequest', {}).get('payload', {}).get('data', {}).get('text', '')
        
        if not user_message:
            logging.error("El mensaje de usuario es nulo o vacío.")
            return jsonify({"fulfillmentText": "Lo siento, no pude entender tu mensaje."})

    except Exception as e:
        logging.error(f"Error al procesar JSON de Dialogflow: {e}")
        return jsonify({"fulfillmentText": "Error interno del servidor al procesar tu solicitud."})
    
    logging.info(f"Mensaje de usuario extraído: {user_message}")

    # 3. Prompt y llamada a la API de Google Gemini
    system_prompt = (
        "Eres un chatbot experto en Inteligencia Artificial Generativa. "
        "Explicas conceptos de forma clara, profesional y amigable."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7
            }
        )

        # 4. Extracción de la respuesta
        answer = response.text
        logging.info("Respuesta de Gemini generada con éxito.")

    except Exception as e:
        logging.error(f"Error en la llamada a la API de Gemini: {e}")
        answer = "Lo siento, hubo un error al conectar con Gemini."

    # 5. Devolver la respuesta a Dialogflow (el formato más simple y seguro)
    return jsonify({
        "fulfillmentText": answer
    })

if __name__ == "__main__":
    # Asegúrate de que el puerto 5000 esté libre
    # El host '0.0.0.0' permite que Serveo se conecte correctamente desde fuera
    app.run(host='0.0.0.0', port=5000, debug=True)
