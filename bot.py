import os
import json
import requests
import telebot

# ----------------------------------------------------------------------
# CONFIGURACIÓN INICIAL
# ----------------------------------------------------------------------
# IMPORTANTE: Reemplaza con el Token de tu Bot obtenido de @BotFather
TOKEN_TELEGRAM = "8632019517:AAHMlr_OuSYBfjPVWyUuFXHWTNf8OeIehI4"

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# Ruta del archivo de configuración (en PythonAnywhere pon la ruta completa)
# Ejemplo: "/home/tu_usuario/telegram_bot/config.json"
CONFIG_FILE = "config.json"


# ----------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ----------------------------------------------------------------------
def leer_configuracion():
    \"\"\"Lee el archivo JSON en cada interacción para verificar parámetros en vivo\"\"\"
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al leer config.json: {e}")
        # Retorno seguro por defecto en caso de falla
        return {"responder_adicionales": True, "mensaje_mantenimiento": "Error de configuración temporal."}

def obtener_tasa_binance_p2p(tipo_operacion):
    \"\"\"
    tipo_operacion: 'BUY' para ver los anuncios de venta (a cuánto compramos)
                    'SELL' para ver los anuncios de compra (a cuánto vendemos)
    \"\"\"
    url = "[https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search](https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search)"
    payload = {
        "asset": "USDT",
        "fiat": "VES",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 3,
        "tradeType": tipo_operacion
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # Nota: Si usas cuenta gratuita de PythonAnywhere, esta solicitud externa podría
        # fallar si Binance bloquea las peticiones desde el proxy gratuito.
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        datos = response.json()
        if datos.get("code") == "000000" and datos.get("data"):
            # Obtenemos el mejor anuncio disponible en la lista
            precio_real = datos["data"][0]["adv"]["price"]
            return float(precio_real)
        return None
    except Exception as e:
        print(f"Error de conexión con Binance P2P: {e}")
        return None


# ----------------------------------------------------------------------
# COMANDOS FIJOS (LOS 5 OBLIGATORIOS)
# ----------------------------------------------------------------------

# 1. Comando: /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    texto = (
        "👋 ¡Bienvenido al Bot Oficial de Monitoreo P2P!\n\n"
        "Este entorno está diseñado exclusivamente para consultas rápidas.\n"
        "Usa /ayuda para ver los comandos que tengo fijados para ti."
    )
    bot.reply_to(message, texto)

# 2. Comando: /ayuda
@bot.message_handler(commands=['ayuda'])
def cmd_ayuda(message):
    texto = (
        "📌 **Comandos fijos disponibles:**\n\n"
        "/start - Iniciar el bot e interactuar.\n"
        "/ayuda - Muestra esta lista de comandos autorizados.\n"
        "/p2p - Consulta el precio real de Compra/Venta de USDT en Venezuela.\n"
        "/estado - Verifica el estado operativo de los módulos del bot.\n"
        "/soporte - Información de contacto y resolución de dudas."
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

# 3. Comando: /p2p (Consulta Binance en tiempo real)
@bot.message_handler(commands=['p2p'])
def cmd_p2p(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    precio_compra = obtener_tasa_binance_p2p("BUY")
    precio_venta = obtener_tasa_binance_p2p("SELL")
    
    if precio_compra and precio_venta:
        texto = (
            "📊 **Tasas de Binance P2P en Tiempo Real** 📊\n"
            "🇻🇪 Market: USDT / VES (Bolívares)\n\n"
            f"🟢 **Precio de Compra:** {precio_compra:.2f} VES\n"
            f"🔴 **Precio de Venta:** {precio_venta:.2f} VES\n\n"
            "_* Valores calculados sobre la tasa del mejor anuncio activo en la plataforma._"
        )
    else:
        texto = "⚠️ No se pudo obtener la información de Binance de forma directa. Intenta de nuevo en unos minutos."
        
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

# 4. Comando: /estado
@bot.message_handler(commands=['estado'])
def cmd_estado(message):
    config = leer_configuracion()
    adicionales_status = "🟢 ACTIVO" if config.get("responder_adicionales") else "🔴 DESACTIVADO (Solo comandos fijos)"
    
    texto = (
        "⚙️ **Estado del Sistema:**\n\n"
        "🔹 Servidor: PythonAnywhere\n"
        "🔹 API Telegram: Conectada\n"
        f"🔹 Respuestas Adicionales: {adicionales_status}"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

# 5. Comando: /soporte
@bot.message_handler(commands=['soporte'])
def cmd_soporte(message):
    texto = (
        "🛠️ **Centro de Soporte Técnico**\n\n"
        "Si experimentas fallas en las lecturas de los scripts de automatización o requieres asistencia con el bot, comunícate con el administrador.\n\n"
        "👤 **Desarrollador:** Administrador del Sistema"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")


# ----------------------------------------------------------------------
# MANEJADOR DE PREGUNTAS ADICIONALES (TEXTO LIBRE)
# ----------------------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def manejar_preguntas_adicionales(message):
    \"\"\"
    Filtra y decide si responder preguntas fuera de los comandos fijos
    según los parámetros actuales del archivo de configuración.
    \"\"\"
    config = leer_configuracion()
    
    # Si tú cambiaste el parámetro a False en el JSON, el bot ejecutará esto:
    if not config.get("responder_adicionales", True):
        # Envía el mensaje de restricción personalizado que guardaste en el archivo
        bot.reply_to(message, config.get("mensaje_mantenimiento", "Modo estricto activo."))
        return
    
    # Si los parámetros permiten conversar, responde de manera habitual:
    texto_respuesta = (
        "💬 Has realizado una consulta libre fuera de mis comandos del menú.\n\n"
        "Como los parámetros de la consola están activos, te confirmo que he recibido tu mensaje: "
        f"_{message.text}_\n\n"
        "Recuerda que para datos precisos debes usar mi barra de comandos fijos."
    )
    bot.reply_to(message, texto_respuesta, parse_mode="Markdown")


# ----------------------------------------------------------------------
# INICIO CONTINUO DEL BOT
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("🚀 El Bot exclusivo de Telegram está corriendo de forma limpia...")
    bot.infinity_polling()
  
