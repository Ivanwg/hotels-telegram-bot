import random
from typing import List, Union, Dict
from .bot_exceptions import NoneTypeError
from telegram_bot_calendar import DetailedTelegramCalendar


class MyStyleCalendar(DetailedTelegramCalendar):
  # previous and next buttons style. they are emoji now!
  # prev_button = "⬅️"
  # next_button = "➡️"
  # you do not want empty cells when month and year are being selected
  empty_month_button = ""
  empty_year_button = ""
  middle_button_year = ""

def return_date_by_lang(defaul_calender_name: str, lang: str, id: int = 0) -> str:
  for_param = ''
  if id == 1:
    for_param = 'заезда' if lang == 'ru' else 'for check-in'
  elif id == 2:
    for_param = 'выезда' if lang == 'ru' else 'for check- out'
  step = defaul_calender_name
  if step == 'year':
    step = 'год' if lang == 'ru' else step
  elif step == 'month':
    step = 'месяц' if lang == 'ru' else step
  elif step == 'day':
    step = 'день' if lang == 'ru' else step
  return ' '.join([step, for_param])


def get_random_list_elem(arr: List[Union[int, str, float]]) -> Union[int, str, float]:
  """Функция, возвращающая рандомный элемент в списке"""
  return random.choice(arr)

def validate_querystring(query: Dict) -> Dict:
  """Функция, возвращающая ошибку NoneTypeError,
  в случае если хотя бы один из ключей в querystring: - объекте параметров для запроса к API, - типа None"""
  for key, value in query.items():
    if type(value) is None or value == '':
      raise NoneTypeError(f'Передано пустое значение в ключ {key}')

  return query