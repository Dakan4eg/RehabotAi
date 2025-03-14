import os
import logging
import redis
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes
from transformers import pipeline

# Конфигурация
REDIS_URL = os.getenv("REDIS_URL")
TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = "microsoft/DialoGPT-small"

# Инициализация
redis_db = redis.from_url(REDIS_URL)
chatbot = pipeline("text-generation", model=MODEL_NAME)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        user_msg = update.message.text
        
        # Сохраняем сообщение
        redis_db.lpush(f"chat_{chat_id}", user_msg)
        redis_db.ltrim(f"chat_{chat_id}", 0, 99)
        
        # Формируем контекст
        history = "\n".join([
            msg.decode() for msg in 
            redis_db.lrange(f"chat_{chat_id}", 0, 99)
        ][::-1])
        
        # Генерируем ответ
        response = chatbot(
            history + "\nBot:",
            max_length=200,
            temperature=0.7
        )[0]['generated_text'].split("Bot:")[-1].strip()
        
        await update.message.reply_text(response[:500])
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("🤖 Ой, что-то сломалось...")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
