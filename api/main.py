import os
import httpx
from google import genai
from fastapi import FastAPI, Request, Response

app = FastAPI()

# Configuración
FB_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_Xfqad--tk24fQ9RbvCK2vb-fW6LdLPj7eiV48XjCOGcT0qGV16sWbTdNsJ8r99D0gj6oeOasa7d/pub?output=csv"

# Inicialización del nuevo cliente para evitar el Warning
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
                    
                    inventario = await obtener_inventario()
                    
                    prompt = f"""
                    Eres un vendedor experto de 'Elite Store Pasto'. 
                    Inventario actual:
                    {inventario}
                    
                    Reglas:
                    1. Responde breve y amable en español de Colombia.
                    2. Da precios exactos del inventario.
                    3. Ubicación: Pasto, Nariño.
                    
                    Mensaje del cliente: {user_msg}
                    """
                    
                    try:
                        # Usando Gemini gemini-3.1-flash-lite-preview
                        response = client.models.generate_content(
                            model='gemini-3.1-flash-lite-preview',
                            contents=prompt
                        )
                        await send_message(sender_id, response.text)
                    except Exception as e:
                        # Si sale el error 429, esto lo imprimirá en los logs
                        print(f"Error con Gemini (posible límite de cuota): {e}")
                        
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
    return Response(content="Error", status_code=403)