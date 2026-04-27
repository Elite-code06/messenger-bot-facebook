import os
import httpx
from google import genai
from fastapi import FastAPI, Request, Response

app = FastAPI()

# Configuración
FB_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_Xfqad--tk24fQ9RbvCK2vb-fW6LdLPj7eiV48XjCOGcT0qGV16sWbTdNsJ8r99D0gj6oeOasa7d/pub?output=csv"

# Cliente con la nueva librería
client = genai.Client(api_key=GEMINI_KEY)

async def obtener_inventario():
    async with httpx.AsyncClient(follow_redirects=True) as client_http:
        try:
            res = await client_http.get(CSV_URL)
            return res.text
        except:
            return "Inventario no disponible."

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
                    prompt = f"Eres un vendedor. Inventario: {inventario}. Responde breve a: {user_msg}"
                    
                    try:
                        # USAR NOMBRE EXACTO PARA EVITAR 404
                        response = client.models.generate_content(
                            model='gemini-3.1-flash-preview',
                            contents=prompt
                        )
                        await send_message(sender_id, response.text)
                    except Exception as e:
                        print(f"Error en Gemini: {e}")
                        
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