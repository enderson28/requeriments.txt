import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configurar logs básicos para ver la actividad en la consola
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 1. Leer variables de entorno (Nunca pegues tus tokens reales aquí)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Instrucciones estrictas para la IA
PROMPT_CONTEXTO = (
    "Eres un asistente virtual automatizado para el canal de atención. Tu único propósito es "
    "responder dudas sobre operaciones internacionales, envío de remesas y recarga/traspaso "
    "de fondos desde bancos nacionales hacia la plataforma Binance utilizando los métodos BpAy y Google Pay (GPay).\n\n"
    "Instrucciones estrictas:\n"
    "1. Sé claro, profesional, cortés y ve directo al punto.\n"
    "2. Si el usuario te pregunta sobre temas ajenos a operaciones internacionales, Binance, BpAy, "
    "Google Pay o transferencias, rechaza la pregunta amablemente diciendo que solo estás entrenado para esos temas.\n"
    "3. Para transferencias con BpAy: Explica que deben transferir a las cuentas autorizadas del canal, "
    "enviar el comprobante y su ID de Binance para acreditar los fondos en un lapso de 5 a 15 minutos.\n"
    "4. Para Google Pay (GPay): Explica que pueden usarlo en Binance P2P con comerciantes que acepten este medio "
    "o solicitar un enlace de cobro seguro con nuestro soporte humano."
)

def consultar_gemini(texto_usuario):
    """
    Realiza una consulta HTTPS directa a la API de Gemini.
    Este método no requiere librerías complejas y respeta perfectamente el proxy de PythonAnywhere.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "parts": [{"text": texto_usuario}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": PROMPT_CONTEXTO}]
        },
        "generationConfig": {
            "temperature": 0.3
        }
    }
    
    # requests detecta el proxy de PythonAnywhere automáticamente
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        try:
            return data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Lo siento, la respuesta de la IA no tiene el formato esperado."
    else:
        logging.error(f"Error de Gemini API: {response.status_code} - {response.text}")
        raise Exception(f"Error API: {response.status_code}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy tu asistente de operaciones internacionales y recargas a Binance.\n"
        "Pregúntame lo que necesites sobre transferencias con BpAy, Google Pay o soporte de transacciones."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Llamar a Gemini usando el método de requests seguro
        respuesta_ia = consultar_gemini(user_text)
        await update.message.reply_text(respuesta_ia, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error al procesar mensaje: {e}")
        await update.message.reply_text(
            "Lo siento, tengo un problema temporal para conectarme con la IA. Por favor, inténtalo de nuevo."
        )

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logging.error("ERROR: Faltan las variables de entorno TELEGRAM_TOKEN o GEMINI_API_KEY.")
        return

    # Proxy obligatorio para que Telegram funcione en la cuenta gratuita de PythonAnywhere
    proxy_url = "http://proxy.server:3128"
    
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .proxy(proxy_url)
        .get_updates_proxy(proxy_url)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot iniciado de forma exitosa en PythonAnywhere. Escuchando...")
    application.run_polling()

if __name__ == '__main__':
    main()
    
