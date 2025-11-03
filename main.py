import os
from google import genai
from dotenv import load_dotenv

# 1. Cargar la API Key de Gemini desde el archivo .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Prompt básico
prompt = "¿Qué tipo de pasatiempos tiene un inmigrante que trabaja duro en su propia tienda de conveniencia?"

# 3. Hacer la llamada a la API
response = client.models.generate_content(
    model="gemini-2.5-flash", # Modelo gratuito y rápido
    contents=prompt, # Se le pasa la variable del prompt directamente
    config={
        "system_instruction": "Tienes que darme la respuesta que más se acerque a lo correcto o verdadero.", #Esta es la instrucción que le daremos al modelo.
        "temperature": 0.5 #Aquí ajustaremos un valor entre 0.0 y 1.0
    }

)

# 4. Mostrar la respuesta en pantalla
print("🤖 Respuesta del modelo:")
print(response.text)