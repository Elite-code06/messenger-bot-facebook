import os
import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

@app.get("/")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), status_code=200)
    return Response(content="Token inválido", status_code=403)

@app.post("/")
async def handle_messages(request: Request):
    data = await request.json()
    print(f"--- NUEVO EVENTO RECIBIDO ---")
    
    if data.get("object") == "page":
        for entry in data.get("entry"):
            for messaging_event in entry.get("messaging"):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")
                    print(f"Mensaje de {sender_id}: {message_text}")
                    
                    # Intentamos responder
                    print("Intentando enviar respuesta...")
                    await send_message(sender_id, f"¡Hola! Soy tu bot de ventas. Recibí tu mensaje: {message_text}")
    
    return Response(content="EVENT_RECEIVED", status_code=200)

async def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(f"RESULTADO ENVÍO: {response.status_code} - {response.text}")
