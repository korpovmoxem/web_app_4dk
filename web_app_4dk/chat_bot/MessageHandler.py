import requests

from web_app_4dk.chat_bot.SendMessage import bot_send_message


def message_add_handler(message):
    random_quote = requests.post(url='http://api.forismatic.com/api/1.0/?method=getQuote&&format=json&lang=ru').json()['quoteText']
    bot_send_message({'dialog_id': message.from_user_id, 'message': f"[I]{random_quote}[/I]"})
