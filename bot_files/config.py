import os
from dotenv import load_dotenv

load_dotenv()


config = {
  'token': os.environ.get('TELEGRAM_TOKEN'),
  'rapidApi': os.environ.get('RAPID_API')
}

BOT_VARIABLES = {
  'hotels_max_count_output': 10,
  'history_max_count_commands': 5,
  'bot_commands_list': ['lowprice', 'highprice', 'bestdeal', 'history'],
  'bot_hello_stickers_list': [
    'CAACAgIAAxkBAAIFfWNzXX12ysy7CsdxIIz_njH54vtjAAJdAANEDc8Xx77nXM4YAjwrBA',
    'CAACAgIAAxkBAAIBJGGhKvrVIMT9zdHKGgckJFdkeygTAAJuBQACP5XMCoY62V2IvLc1IgQ',
    'CAACAgIAAxkBAAEGbQtjc13wOPRnSYqd_x-_FyYTXwYH0gACoAADlp-MDmce7YYzVgABVSsE',
    'CAACAgIAAxkBAAEGbRljc15NhNBAzGfXU05AgerMbWeyfAACdAwAAra7OEuOzqfMQMSAJSsE',
    'CAACAgIAAxkBAAEGbR1jc15jaEz5MmHchNS7W8PVnXzFnAACbwADmL-ADeFz2TIaBadIKwQ'
  ],
  'bot_sorry_stickers_list': [
    'CAACAgIAAxkBAAEGbxxjc9iMCUpXpShY_7SXD6qbEp74lgACeg0AAlhngEq9GIx3x9cX7SsE'
  ]
}