import os
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Update
import iol_api
from dotenv import load_dotenv

# Cargamos variables del archivo .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buenas, soy el bot. Tu mensaje es: " + update.message.text)

# Cotización de cauciones desde IOL
async def cauciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = iol_api.cotizacion_cauciones()
        mensaje = "📊 *Cauciones disponibles en BCBA:*\n\n"
        for c in data[:5]:
            mensaje += f"• Plazo: {c['plazo']} días | Tasa: {c['tasa']}% | Último: {c['ultimoPrecio']}\n"
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al obtener cauciones: {e}")

def main():
    bot = Application.builder().token(TELEGRAM_TOKEN).build()
    bot.add_handler(CommandHandler("cauciones", cauciones))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()