from fastapi import FastAPI, Request, Response
import os

app = FastAPI()

# Configura estos en las variables de entorno de Vercel
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.get("/")
async def verify(request: Request):
    # Meta envía una petición GET para validar tu servidor
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), status_code=200)
    return Response(content="Token de verificación inválido", status_code=403)

@app.post("/")
async def handle_messages(request: Request):
    data = await request.json()
    # Aquí llegará el JSON con los mensajes de los usuarios
    if data.get("object") == "page":
        for entry in data.get("entry"):
            for messaging_event in entry.get("messaging"):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    text = messaging_event["message"].get("text")
                    print(f"Mensaje de {sender_id}: {text}")
    return Response(content="EVENT_RECEIVED", status_code=200)
