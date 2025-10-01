# main.py
# ─────────────────────────────────────────────────────────────────────────────
# Запуск:  python main.py
# Требования: aiogram v3, openai v1
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import logging
from collections import defaultdict, deque
from typing import Deque, Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from openai import OpenAI

# ── ВСТАВЬТЕ СВОИ ДАННЫЕ ─────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "8163163974:AAGhRWxV8qi5OKN4uBQyzg4PWvbKlhj_u14"
print(OPENAI_API_KEY)  # для проверки
CONTEXT            = (
    "Вы — внимательный и лаконичный ассистент. Отвечайте по делу, "
    "NEUROCHIEF - это компания которая создаёт умных чат-ботов с ИИ, нейроассистентов, нейропродавцов. Также"
    "занимается разработкой автоматизированных систем для оптимизации бизнеса. С полной информацией и с нашими услугами вы можете ознакомиться на нашем сайте https://neurochief.ru/"
)
# ─────────────────────────────────────────────────────────────────────────────

# Настройки модели и памяти
MODEL_NAME = "gpt-4o-mini"   # при необходимости замените на доступную вам модель
TEMPERATURE = 0.4
MAX_TURNS_PER_USER = 8        # хранить последние 8 реплик пользователя (и ответов ассистента)

# Логи
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("tg-gpt-bot")

# Инициализация клиентов
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
oaiclient = OpenAI(api_key=OPENAI_API_KEY)

# История диалогов в RAM: {user_id: deque([{"role": "user"/"assistant", "content": "..."}, ...])}
DialogHistory = Dict[int, Deque[dict]]
history: DialogHistory = defaultdict(lambda: deque(maxlen=MAX_TURNS_PER_USER * 2))


def build_messages(user_id: int, user_text: str) -> List[dict]:
    """
    Формируем массив сообщений для Chat Completions:
    1) системный CONTEXT
    2) сжатая история диалога
    3) текущий запрос пользователя
    """
    msgs: List[dict] = [{"role": "system", "content": CONTEXT}]
    msgs.extend(list(history[user_id]))
    msgs.append({"role": "user", "content": user_text})
    return msgs


def ask_openai(messages: List[dict]) -> str:
    """
    Синхронный вызов OpenAI (вынесен в отдельный поток, чтобы не блокировать event loop).
    """
    resp = oaiclient.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return (resp.choices[0].message.content or "").strip() or "Извините, у меня нет ответа."


def split_telegram_text(text: str, limit: int = 4096) -> List[str]:
    """
    Безопасно разбивает длинный текст на части по лимиту Telegram.
    """
    parts: List[str] = []
    t = text
    while t:
        if len(t) <= limit:
            parts.append(t)
            break
        chunk = t[:limit]
        # стараться резать по переводу строки/точке
        cut = max(chunk.rfind("\n"), chunk.rfind("."))
        if cut <= 0:
            cut = limit
        parts.append(t[:cut].rstrip())
        t = t[cut:].lstrip()
    return parts


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот на базе ChatGPT.\n"
        "Напишите сообщение — отвечу с учётом контекста.\n\n"
        "Доступные команды:\n"
        "• /help — как пользоваться\n"
        "• /reset — очистить историю диалога"
    )


@dp.message(Command("help"))
async def on_help(message: Message) -> None:
    await message.answer(
        "Просто отправьте текст — и я отвечу, учитывая прошлую переписку.\n"
        "Команда /reset очищает историю для вашего пользователя."
    )


@dp.message(Command("reset"))
async def on_reset(message: Message) -> None:
    history.pop(message.from_user.id, None)
    await message.answer("История диалога очищена ✅")


@dp.message(F.text)  # реагируем на любой текст
async def on_text(message: Message) -> None:
    user_id = message.from_user.id
    user_text = (message.text or "").strip()
    if not user_text:
        return

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):

        try:
            messages = build_messages(user_id, user_text)

            # вызываем OpenAI в отдельном потоке (SDK — синхронный)
            reply: str = await asyncio.to_thread(ask_openai, messages)

            # сохраняем историю
            history[user_id].append({"role": "user", "content": user_text})
            history[user_id].append({"role": "assistant", "content": reply})

            # учитываем лимит 4096 символов у Telegram
            for part in split_telegram_text(reply):
                await message.answer(part)

        except Exception as e:
            log.exception("Ошибка OpenAI")
            await message.answer(
                "Упс, что-то пошло не так. Попробуйте ещё раз позже.\n"
                f"Техническая деталь: {type(e).__name__}"
            )


async def main() -> None:
    log.info("Bot starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped.")