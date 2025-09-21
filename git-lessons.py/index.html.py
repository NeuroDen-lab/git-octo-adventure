import telebot

TOKEN = "8163163974:AAGhRWxV8qi5OKN4uBQyzg4PWvbKlhj_u14"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

bot.polling()
