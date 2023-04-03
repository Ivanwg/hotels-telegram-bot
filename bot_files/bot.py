from typing import Optional, Union
import telebot
from telebot import types
from .bot_requests import fetch_result_by_command
from .config import config, BOT_VARIABLES
from .user import User
from .help_funcs import get_random_list_elem, return_date_by_lang, MyStyleCalendar
from .bot_exceptions import NoneTypeError, ServerSilence, IncorrectCity
from telegram_bot_calendar import LSTEP
from datetime import date, timedelta
from .db_peewee import create_table, get_calls_history, Call, Result
from peewee import *


bot = telebot.TeleBot(config['token'], parse_mode=None)
types.ReplyKeyboardRemove()

def help(text: Optional[str] = None) -> str:
  output = 'Список моих команд:\n' \
           '/lowprice - узнать топ самых дешёвых отелей в городе\n' \
           '/highprice - узнать топ самых дорогих отелей в городе\n' \
           '/bestdeal - узнать топ отелей, наиболее подходящих по цене и расположению от центра\n' \
           '/history - узнать историю поиска отелей'
  if text:
    text = text + '\n' + output
    return text
  else:
    return output

def create_send_final_message(chat_id: int) -> None:
  user = User.get_user(chat_id)
  result = []
  if user.command == 'history':
    commands = get_calls_history(chat_id)
    text_output = 'Вывожу историю поиска отелей👇\n\n\n'
    if len(commands):
      for command in commands:
        default_letter = '?'
        command_text = '✅ команда "<b>{command}</b>"\n была вызвана <b>{date}</b>\n\n' \
                       'Найденные отели в {city}:\n'.format(command=command.get('command_name', default_letter),
                                                            date=command.get('date', default_letter),
                                                            city=command.get('city', default_letter))

        for i, db_hotel in enumerate(command.get('hotels')):
          try:
            hotel_text = '{index}) <a href="{url}">{name}</a>\n'.format(index=i+1, url=db_hotel['hotel_url'],
                                                                      name=db_hotel['hotel_name'])
          except (KeyError, ValueError) as err:
            hotel_text = 'Информация о {index} отеле пропала'.format(index=i+1)
          command_text += hotel_text
        command_text += '\n\n'
        text_output += command_text
      bot.send_message(chat_id, text_output, parse_mode='html', disable_web_page_preview=True)
    else:
      bot.send_message(chat_id, 'Кажется, Вы еще не запрашивали отели...',
                       parse_mode='html', disable_web_page_preview=True)
    return
  else:
    try:
      result = fetch_result_by_command(user)
    except (NoneTypeError, ServerSilence, IncorrectCity) as err:
      print(err)
      on_not_found(chat_id=chat_id, err_text=err)
      return
  if not len(result):
    on_not_found(chat_id)
    return
  call = Call.create(chat_id=chat_id, city=user.city, command=user.command)
  for hotel in result:
    text_to_send = '<b>{name}</b>\n' \
                   '<i>адрес:</i> {address}\n' \
                   '<i>расстояние от центра:</i> {distance}\n' \
                   '<i>цена за ночь:</i> {price}\n' \
                   '<i>суммарно:</i> {total}\n' \
                   '<a href="{link}">Перейти на страницу отеля</a>\n'.format(name=hotel['name'],
                                                                              address=hotel['address'],
                                                                              distance=hotel['distance_from_center'],
                                                                              price=hotel['price'],
                                                                              total=hotel['price_total'],
                                                                              link=hotel['link'])
    hotel_db = Result.create(call=call, hotel_name=hotel['name'], hotel_url=hotel['link'])
    bot.send_message(chat_id, text_to_send, parse_mode='html', disable_web_page_preview=True)
    if len(hotel['photos']):
        medias = [types.InputMediaPhoto(photo_link) for photo_link in hotel['photos']]
        try:
          bot.send_media_group(chat_id, media=medias)
        except telebot.apihelper.ApiTelegramException as err:
          bot.send_message(chat_id, 'Полученные изображения удалены с сервера.\n'
                                    'Советуем посмотреть фото отеля по ссылке')
        # for photo_link in hotel['photos']:
        #   bot.send_photo(chat_id, photo_link)

@bot.message_handler(commands=['start'])
def welcome(message) -> None:
  bot.send_sticker(message.chat.id, get_random_list_elem(BOT_VARIABLES['bot_hello_stickers_list']))
  bot.send_message(message.chat.id, f'Добро пожаловать, {message.from_user.first_name}!\n'
                                    f'Я - <b>{bot.get_me().first_name}</b>, бот компании <b>Too Easy Travel</b>,\n'
                                    f'созданный, чтобы помочь Вам найти отель.', parse_mode='html')
  bot.send_message(message.chat.id, help('Давайте начнем:)'))


@bot.message_handler(commands=['help'])
def send_help_message(message) -> None:
  bot.send_message(message.chat.id, help('Всегда готов помочь Вам😉'))


@bot.message_handler(commands=BOT_VARIABLES['bot_commands_list'])
def define_command_logic(message) -> None:
  command = message.text.replace('/', '')

  user = User.get_user(message.chat.id)
  user.lang = message.from_user.language_code
  user.command = command

  if command != 'history':
    ask_city(message)
  else:
    create_send_final_message(message.chat.id)


def ask_city(message) -> None:
  """Функция,запрашивающая город"""
  msg = bot.send_message(message.chat.id, 'В каком городе будем искать отель?')
  bot.register_next_step_handler(msg, ask_date_after_city)


def ask_date_after_city(message) -> None:
  """Функция,идущая после запроса города и вызывающая калерндарь заезда"""
  user = User.get_user(message.chat.id)
  user.city = message.text
  ask_date(chat_id=message.chat.id, calendar_id=1)


def ask_date(chat_id, calendar_id=0) -> None:
  """Функция,запрашивающая дату"""
  user = User.get_user(chat_id)
  min_date = user.check_in + timedelta(days=1) if calendar_id == 2 else date.today()
  lang = 'ru' if user.lang == 'ru_RU' else 'en'
  select = 'Выберите' if lang == 'ru' else 'Select'
  # календарь при дате выезда не работает должным образом в виде кнопок года
  calendar, step = MyStyleCalendar(current_date=date.today(), min_date=min_date,
                                   max_date=date.today() + timedelta(days=1000),
                                   calendar_id=calendar_id, locale=lang).build()
  lang_step = return_date_by_lang(LSTEP[step], lang, calendar_id)
  bot.send_message(chat_id,
                   f'{select} {lang_step}',
                   reply_markup=calendar)


@bot.callback_query_handler(func=MyStyleCalendar.func(calendar_id=1))
def cal(call):
  """Handler для даты заезда"""
  user = User.get_user(call.message.chat.id)
  lang = 'ru' if user.lang == 'ru_RU' else 'en'
  result, key, step = MyStyleCalendar(current_date=date.today(), min_date=date.today(),
                                      max_date=date.today() + timedelta(days=1000),
                                      calendar_id=1, locale=lang).process(call.data)
  lang_step = return_date_by_lang(LSTEP[step], lang, 1)
  if not result and key:
    select = 'Выберите' if lang == 'ru' else 'Select'
    bot.edit_message_text(f'{select} {lang_step}',
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=key)
  elif result:
    user.check_in = result
    text = 'Вы выбрали' if lang == 'ru' else 'You selected'
    bot.edit_message_text(f'{text} {result}',
                          call.message.chat.id,
                          call.message.message_id)
    ask_date(call.message.chat.id, calendar_id=2)

@bot.callback_query_handler(func=MyStyleCalendar.func(calendar_id=2))
def cal(call):
  """Handler для даты выезда"""
  user = User.get_user(call.message.chat.id)
  lang = 'ru' if user.lang == 'ru_RU' else 'en'
  min_date = user.check_in + timedelta(days=1)
  max_date = user.check_in + timedelta(days=1000)
  result, key, step = MyStyleCalendar(current_date=date.today(), min_date=min_date,
                                      max_date=max_date,
                                      calendar_id=2, locale=lang).process(call.data)
  lang_step = return_date_by_lang(LSTEP[step], lang, 2)
  if not result and key:
    select = 'Выберите' if lang == 'ru' else 'Select'
    bot.edit_message_text(f'{select} {lang_step}',
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=key)
  elif result:
    user.check_out = result
    text = 'Вы выбрали' if lang == 'ru' else 'You selected'
    bot.edit_message_text(f'{text} {result}',
                          call.message.chat.id,
                          call.message.message_id)
    ask_hotels(chat_id=call.message.chat.id)

def ask_hotels(chat_id) -> None:
  """Функция, запрашивающая ко-во отелей на вывод"""
  user = User.get_user(chat_id)
  msg = bot.send_message(chat_id, 'Сколько вывести отелей?')
  if user.command in ['lowprice', 'highprice']:
    bot.register_next_step_handler(msg, photos_need)
  elif user.command == 'bestdeal':
    bot.register_next_step_handler(msg, ask_price_min)


def create_new_price_inline_keyboard(view_content: Union[str, int],
                                     lang: str,
                                     submit: str = 'submit_for_min') -> types.InlineKeyboardMarkup:
  keyboard = types.InlineKeyboardMarkup()
  keyboard.row_width = 3
  plus_item = types.InlineKeyboardButton(text='➕', callback_data='plus')
  view_item = types.InlineKeyboardButton(text=f'{view_content}', callback_data='price_ignore')
  minus_item = types.InlineKeyboardButton(text='➖', callback_data='minus')
  submit_text = 'Подтвердить' if lang == 'ru_RU' else 'Submit'
  submit_item = types.InlineKeyboardButton(text=f'{submit_text}', callback_data=f'{submit}')
  keyboard.add(minus_item, view_item, plus_item, submit_item)

  return keyboard


def ask_price_min(message,  price_content: int = 50) -> None:
  """Функция, запрашивающая минимальную цену от пользователя"""
  user = User.get_user(message.chat.id)
  user.hotels_count = message.text
  keyboard = create_new_price_inline_keyboard(view_content=price_content, lang=user.lang)
  bot.send_message(message.chat.id, 'Давайте определим минимальный диапазон цен в 💲:',
                   reply_markup=keyboard)

def ask_price_max(chat_id, price_content: int = 1000) -> None:
  """Функция, запрашивающая максимальную цену от пользователя"""
  user = User.get_user(chat_id)
  keyboard = create_new_price_inline_keyboard(view_content=price_content,
                                              lang=user.lang,
                                              submit='submit_for_max')
  bot.send_message(chat_id, 'Давайте определим максимальный диапазон цен в 💲:', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ['plus', 'minus', 'submit_for_min', 'submit_for_max',
                                                            'submit_for_dest_max', 'submit_for_dest_min'])
def change_price(call) -> None:
  """Функция изменения значения в блоке кнопок - value + """
  user = User.get_user(call.message.chat.id)
  last_keyboard = call.message.reply_markup.keyboard[0]
  view_content = last_keyboard[1].text
  submit_content = call.message.reply_markup.keyboard[1][0].callback_data
  last_text = call.message.text
  change_value = 10
  if submit_content in ['submit_for_dest_max', 'submit_for_dest_min']:
    change_value = 1
  if call.data in ['plus', 'minus']:
    user_param_min = 0
    if submit_content in ['submit_for_max']:
      user_param_min = 0 if user.price_min is None else user.price_min
    elif submit_content in ['submit_for_dest_max']:
      user_param_min = 0 if user.distance_from_center_min is None else user.distance_from_center_min
    if call.data == 'minus' and (int(view_content) - change_value < 0 or
                                 int(view_content) - change_value < user_param_min):
      return
    new_view = int(view_content) + change_value if call.data == 'plus' else int(view_content) - change_value
    new_view_content = '{new_content}'.format(new_content=new_view)
    new_keyboard = create_new_price_inline_keyboard(view_content=new_view_content,
                                                    lang=user.lang,
                                                    submit=submit_content)
    try:
      bot.edit_message_text(chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=f'{last_text}',
                            reply_markup=new_keyboard)
    except telebot.apihelper.ApiTelegramException:
      pass
  elif call.data == 'submit_for_min':
    user.price_min = view_content
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f'Ищем отели в диапазанe от {view_content}$',
                          reply_markup=None)
    ask_price_max(call.message.chat.id)
  elif call.data == 'submit_for_max':
    if int(view_content) < user.price_min:
      return
    user.price_max = view_content
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f'Ищем отели в диапазанe до {view_content}$',
                          reply_markup=None)
    photos_need(chat_id=call.message.chat.id)
    # ask_center_destination_min(call.message.chat.id)
  # elif call.data == 'submit_for_dest_min':
  #   user.distance_from_center_min = view_content
  #   bot.edit_message_text(chat_id=call.message.chat.id,
  #                         message_id=call.message.message_id,
  #                         text=f'Ищем отели на минимальном расстоянии от центра в {view_content} км.',
  #                         reply_markup=None)
  #   ask_center_destination_max(call.message.chat.id)
  # elif call.data == 'submit_for_dest_max':
  #   if int(view_content) < user.distance_from_center_min:
  #     return
  #   user.distance_from_center_max = view_content
  #   bot.edit_message_text(chat_id=call.message.chat.id,
  #                         message_id=call.message.message_id,
  #                         text=f'Ищем отели на максимальном расстоянии от центра в {view_content} км.',
  #                         reply_markup=None)
  #   photos_need(chat_id=call.message.chat.id)


def ask_center_destination_min(chat_id, view_content: int = 5) -> None:
  """Функция, запрашивающая минимальное расстояние от центра города"""
  user = User.get_user(chat_id)
  keyboard = create_new_price_inline_keyboard(view_content=view_content,
                                     lang=user.lang,
                                     submit='submit_for_dest_min')
  bot.send_message(chat_id, 'Давайте определим минимальное желаемое расстояние от центра в км.:',
                   reply_markup=keyboard)

def ask_center_destination_max(chat_id, view_content: int = 10) -> None:
  """Функция, запрашивающая максимальное расстояние от центра города"""
  user = User.get_user(chat_id)
  keyboard = create_new_price_inline_keyboard(view_content=view_content,
                                     lang=user.lang,
                                     submit='submit_for_dest_max')
  bot.send_message(chat_id, 'Давайте определим максимальное желаемое расстояние от центра в км.:',
                   reply_markup=keyboard)

def photos_need(message: Optional[telebot.types.Message] = None, chat_id: Optional[int] = None) -> None:
  """Функция, запрашивающая необходимость вывода фото"""
  message_chat_id = message.chat.id if message else chat_id
  user = User.get_user(message_chat_id)
  if message:
    user.hotels_count = message.text

  keyboard = types.InlineKeyboardMarkup()
  yes_item = types.InlineKeyboardButton(text='ДА', callback_data='yes')
  no_item = types.InlineKeyboardButton(text='НЕТ', callback_data='no')
  keyboard.add(yes_item, no_item)
  call = bot.send_message(message_chat_id, 'Нужно ли вывести фото отелей?', reply_markup=keyboard)
  # bot.register_next_step_handler(msg, photos_count, **user_dict)
  # bot.register_callback_query_handler(call, photos_count)

@bot.callback_query_handler(func=lambda call: call.data in ['yes', 'no'])
def photos_count(call) -> None:
  user = User.get_user(call.message.chat.id)

  if call.data == 'yes':
    user.load_image = True
    msg = bot.send_message(call.message.chat.id, 'Сколько вывести фотографий отеля?')
    bot.register_next_step_handler(msg, ask_photo_count)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Отличное решение!)",
                          reply_markup=None)
  elif call.data == 'no':
    user.load_image = False
    bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Ok, понял, выводим без фото:)",
                                reply_markup=None)
    bot.send_message(call.message.chat.id, 'Минуточку, обрабатываю запрос...')
    create_send_final_message(call.message.chat.id)


def ask_photo_count(message) -> None:
  user = User.get_user(message.chat.id)
  user.load_image_count = message.text
  bot.send_message(message.chat.id, 'Минуточку, обрабатываю запрос...')
  create_send_final_message(message.chat.id)


def on_not_found(chat_id: int, err_text: Union[str, Exception] = 'Что-то пошло не так...\nПопробуйте снова'):
  bot.send_message(chat_id, err_text)
  bot.send_sticker(chat_id, get_random_list_elem(BOT_VARIABLES['bot_sorry_stickers_list']))

@bot.message_handler(content_types=["sticker"])
def default_sticker(message):
  bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEGhihjfkv0KMXLBrDkoXQa9wklfqo6WgACXwkAAhhC7ghT5M1UMfGUOisE')

@bot.message_handler(func=lambda message: True)
def default(message):
  bot.send_message(message.chat.id, 'Я не могу вас понять:(\nЧтобы увидеть список моих команд, используйте /help')

def run_bot() -> None:
  create_table()
  bot.infinity_polling()
