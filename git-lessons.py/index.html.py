import telebot

TOKEN = "8163163974:AAGhRWxV8qi5OKN4uBQyzg4PWvbKlhj_u14"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

bot.polling()
import telebot
import openai

TELEGRAM_TOKEN = "8163163974:AAGhRWxV8qi5OKN4uBQyzg4PWvbKlhj_u14"
OPENAI_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

@bot.message_handler(func=lambda message: True)
def gpt_reply(message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message.text}]
    )
    answer = response["choices"][0]["message"]["content"]
    bot.reply_to(message, answer)

bot.polling()
