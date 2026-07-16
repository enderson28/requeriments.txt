import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
# Configurar logs para ver el estado del bot en la consola de Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO)
# Obtener Tokens de manera segura desde las variables de entorno de Render
TELEGRAM_TOKEN = os.getenv("8632019517:AAGDJQBkJMdRRCwXrEfaoct3DkQSD-CZ-ZA")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6L3NW7UAQKxGp-nhe8lP747i2Dc42xaoHh__IyRXbnMMA")
# Inicializar cliente de Gemini
ai_client = genai.Client(api_key=GEMINI_API_KEY)
# Instrucciones del sistema para definir la personalidad y reglas de la IA
PROMPT_CONTEXTO = (
"Eres un asistente virtual automatizado para el canal de atención. Tu único propósito es " "responder dudas sobre operaciones internacionales, envío de remesas y recarga/traspaso "
"de fondos desde bancos nacionales hacia la plataforma Binance utilizando los métodos
Bpay y Google Pay (GPay).\n\n"
"Instrucciones estrictas:\n"
"1. Sé claro, profesional, cortés y ve directo al punto.\n"
"2. Si el usuario te pregunta sobre temas ajenos a operaciones intercambiarias, Binance,
Bpay, "
"Google Pay o transferencias, rechaza la pregunta amablemente diciendo que solo estás
entrenado para esos temas.\n"
"3. Para Depósitos con Bpay: Explica que deben hacer el traspaso por medio de Bpay ( Deposito USD ) a las opciones autorizadas del
canal Binance, "
"4. Para Google Pay (GPay): Explica que pueden usarlo en Binance P2P con comerciantes
que acepten este medio o por medio del sistema VES ( Deposito USD )  "
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Envía un mensaje de bienvenida cuando se ejecuta /start."""
await update.message.reply_text(
"¡Hola! Soy tu asistente de operaciones intercambiarias y deposito a Binance.\n"
"Pregúntame lo que necesites sobre transferencias con Bpay, Google Pay o soporte de
transacciones."
)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Recibe la pregunta del usuario, la procesa con Gemini y le responde."""
user_text = update.message.text
# Mostrar que el bot está "escribiendo" en Telegram
await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
try:
# Llamar a la API gratuita de Gemini
response = ai_client.models.generate_content(
model='gemini-2.5-flash',
contents=user_text,
config=types.GenerateContentConfig(
system_instruction=PROMPT_CONTEXTO,
temperature=0.3, # Baja temperatura para máxima precisión financiera
),
)
respuesta_ia = response.text
await update.message.reply_text(respuesta_ia, parse_mode="Markdown")
except Exception as e: logging.error(f"Error al llamar a Gemini: {e}")
await update.message.reply_text(
"Lo siento, en este momento tengo problemas para procesar tu consulta. "
"Por favor, intenta de nuevo en unos minutos o escribe directamente a soporte
tecnico."
)
def main():
"""Inicia el bot de Telegram."""
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
logging.error("Faltan variables de entorno TELEGRAM_TOKEN o GEMINI_API_KEY.")
return
application = Application.builder().token(TELEGRAM_TOKEN).build()
# Agregar los manejadores
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
handle_message))
logging.info("Bot iniciado y escuchando mensajes...")
application.run_polling()
if __name__ == '__main__':
main()

