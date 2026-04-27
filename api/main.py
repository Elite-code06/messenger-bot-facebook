import os
import httpx
# 1. Importación correcta de la nueva librería
from google import genai
from fastapi import FastAPI, Request, Response

app = FastAPI()

# Configuración desde variables de entorno
FB_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_Xfqad--tk24fQ9RbvCK2vb-fW6LdLPj7eiV48XjCOGcT0qGV16sWbTdNsJ8r99D0gj6oeOasa7d/pub?output=csv"

# 2. Inicialización del nuevo cliente
client = genai.Client(api_key=GEMINI_KEY)

async def obtener_inventario():
    async with httpx.AsyncClient() as client_http:
        try:
            res = await client_http.get(CSV_URL)
            return res.text
        except Exception as e:
            print(f"Error al obtener inventario: {e}")
            return "No hay datos de inventario disponibles."

@app.post("/")
async def handle_messages(request: Request):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry"):
            for event in entry.get("messaging"):
                if event.get("message"):
                    sender_id = event["sender"]["id"]
                    user_msg = event["message"].get("text")
                    
                    # Descargamos el inventario actual
                    inventario = await obtener_inventario()
                    
                    # Prompt optimizado para Gemini 2.0 Flash
                    prompt = f"""
                    Eres un vendedor experto de 'Elite Store Pasto'. 
                    Tu objetivo es ayudar a los clientes usando este inventario:
                    {inventario}
                    
                    Reglas de oro:
                    1. Responde de forma muy breve, amable y en español de Colombia.
                    2. Si preguntan precio o info, dalo exactamente como aparece en el inventario.
                    3. Nuestra ubicación física es en Pasto, Nariño.
                    4. Si un producto NO está en el inventario, di que no lo tenemos por ahora.
                    5. No inventes datos que no estén en el texto del inventario.
                    
                    Mensaje del cliente: {user_msg}
                    """
                    
                    try:
                        # 3. Llamada a Gemini 2.0 Flash usando el nuevo cliente
                        response = client.models.generate_content(
                            model='gemini-2.0-flash',
                            contents=prompt
                        )
                        await send_message(sender_id, response.text)
                    except Exception as e:
                        print(f"Error con Gemini: {e}")
                        
    return Response(content="EVENT_RECEIVED", status_code=200)

async def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    async with httpx.AsyncClient() as client_http:
        await client_http.post(url, json=payload)

@app.get("/")
async def verify(request: Request):
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if token == os.getenv("VERIFY_TOKEN"):
        return Response(content=challenge)
    return Response(content="Error de verificación", status_code=403)