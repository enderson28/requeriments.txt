import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Configurar logs básicos
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 1. Leer variables de entorno (Asegúrate de configurarlas en la consola de Bash primero)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Configurar cliente de Gemini 
# El SDK oficial detectará el proxy HTTP de PythonAnywhere de forma automática
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Instrucciones de comportamiento para la IA
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy tu asistente de operaciones internacionales y recargas a Binance.\n"
        "Pregúntame lo que necesites sobre transferencias con BpAy, Google Pay o soporte de transacciones."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_CONTEXTO,
                temperature=0.3,
            ),
        )
        await update.message.reply_text(response.text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error al llamar a Gemini: {e}")
        await update.message.reply_text(
            "Lo siento, tengo un problema temporal para procesar tu consulta. Inténtalo de nuevo."
        )

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logging.error("ERROR: Faltan las variables de entorno TELEGRAM_TOKEN o GEMINI_API_KEY.")
        return

    # 3. Configurar Telegram para que use el PROXY obligatorio de PythonAnywhere
    # Si no se define este proxy, Telegram no podrá recibir ni enviar mensajes en cuentas gratis.
    proxy_url = "http://proxy.server:3128"
    
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .proxy(proxy_url)          # <--- ¡ESTO EVITA EL BLOQUEO DE PYTHONANYWHERE!
        .get_updates_proxy(proxy_url)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot iniciado de forma exitosa en PythonAnywhere. Escuchando...")
    application.run_polling()

if __name__ == '__main__':
    main()
                
            
