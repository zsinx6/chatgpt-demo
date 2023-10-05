import os

import logging
from dotenv import load_dotenv
from httpx import AsyncClient, Timeout
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING
)
logger = logging.getLogger(__name__)


load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
assert OPENAI_KEY
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
assert TELEGRAM_TOKEN
TELEGRAM_ID = os.getenv("TELEGRAM_ID")
assert TELEGRAM_ID
default_temp = None


async def handle_user_id(user_id, update, context):
    if str(user_id) != str(TELEGRAM_ID):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Usuário não autorizado."
        )
        logger.warning(f"Usuário não autorizado: {user_id}")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await handle_user_id(update.effective_user.id, update, context):
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Olá, eu sou um bot de exemplo para a semana da química.",
    )


async def set_temperature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await handle_user_id(update.effective_user.id, update, context):
        return
    global default_temp
    temp = None
    try:
        temp = update.message.text.split()[1]
        assert 0 <= float(temp) <= 1
        default_temp = float(temp)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Temperatura alterada para {default_temp}",
        )
    except Exception:
        logger.warning(f"Temperatura inválida: {temp}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="O valor deve ser numérico entre 0 e 1",
        )


async def call_chatgpt(prompt, update, context):
    json_body = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-4",
    }
    if default_temp:
        json_body["temperature"] = default_temp

    async with AsyncClient() as client:
        timeout = Timeout(30.0, read=240.0)
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json=json_body,
            timeout=timeout,
        )
        if response.status_code != 200:
            await error_message(update, context)
            return
        try:
            chatgpt_text = response.json()["choices"][0]["message"]["content"]
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=chatgpt_text
            )
        except Exception:
            await error_message(update, context)
            return


async def error_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("Erro na chamada para a openai")
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Erro na chamada para a openai"
    )


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await handle_user_id(update.effective_user.id, update, context):
        return
    try:
        prompt = update.message.text
        await call_chatgpt(prompt, update, context)
    except Exception:
        await error_message(update, context)


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    text_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), text_message
    )
    start_handler = CommandHandler("start", start)
    set_temperature_handler = CommandHandler("set_temperature", set_temperature)
    application.add_handler(start_handler)
    application.add_handler(text_message_handler)
    application.add_handler(set_temperature_handler)
    application.run_polling()
