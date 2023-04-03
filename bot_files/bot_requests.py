from typing import Dict, Optional, List, Union
from .user import User
from .bot_exceptions import NoneTypeError, IncorrectCity, ServerSilence
from .help_funcs import validate_querystring
from .config import config
import requests
import json
# import db
import datetime


def fetch_rapid_api(method: str, url: str, querystring_to_validate: Dict) -> Dict:
  headers = {
    'X-RapidAPI-Key': config['rapidApi'],
    'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'
  }
  if method == 'POST':
    headers['content-type'] = 'application/json'
  res = {}
  try:
    querystring = validate_querystring(querystring_to_validate)
  except NoneTypeError as err:
    print(err)
    return res
  else:
    for i in range(3):
      try:
        response = requests.request(method,
                                    url,
                                    headers=headers,
                                    params=querystring,
                                    timeout=10) if method == 'GET' else requests.request(method,
                                                                                         url,
                                                                                         headers=headers,
                                                                                         json=querystring,
                                                                                         timeout=10)
      except requests.exceptions.Timeout:
        print("Timeout occurred")
        if i != 2:
          print('Пробуем еще раз')
        continue
      else:
        if response.status_code == 200:
          res = response.json()

          return res
        break
    else:
      raise ServerSilence()

  return res


def get_id(dict_with_id: Dict) -> Optional[int]:

  """Функция для извлечения ID из полученного от API ответа в виде Dict"""

  destination_id = None
  try:
    destination_id = dict_with_id['suggestions'][0]['entities'][0]['destinationId']
  except (KeyError, ValueError) as err:
    print(err)
    print('Разработчики изменили ключи для поиска ID города')
  finally:
    return destination_id



def fetch_destination_id(city: str, lang: str = 'ru_RU') -> Optional[int]:

  """Функция для запроса ID,
   указываемого пользователем субъекта (город, страна и т.д.)"""

  url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
  querystring_to_validate = {'query': f'{city}', 'locale': f'{lang}'}
  try:
    res = fetch_rapid_api('GET', url, querystring_to_validate)
    destination_id = get_id(res)
  except ServerSilence as err:
    raise err
  else:
    return destination_id



def fetch_hotel_detail(hotel_id: int, user: 'User') -> Dict:

  """Функция для запроса фото информации об отеле по его ID
  (фото, адрес и т.д.)"""

  url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
  querystring_to_validate = {'id': f'{hotel_id}'}

  try:
    res = fetch_rapid_api('GET', url, querystring_to_validate)
    if not res.get('hotelImages'):
      print('фото отеля нет')
    # elif not res.get('roomImages'):
    #   print('фото комнат отеля тоже')
      raise NoneTypeError('На сервере отсутствуют фото отеля')
  except ServerSilence as err:
    raise err
  else:
    return res

def get_necessary_img_count(img_list: List, is_photos: bool = False, count: int = 0) -> List:

  """Функция для получения необходимого количества url изображения отелей из response"""

  url_list = []
  if len(img_list) > 0 and is_photos:
    for img_dict in img_list[:count]:
      url = img_dict.get('baseUrl')
      if url:
        size = img_dict['sizes'][0]['suffix']
        formatted_url = url.format(size=size)
        url_list.append(formatted_url)

  return url_list

def filter_hotels(list_to_filter: List, user: 'User') -> List:
  if user.command in ['lowprice', 'highprice']:
    return list_to_filter
  elif user.command == 'bestdeal':
    return  list_to_filter
  # elif user.command == 'bestdeal':
  #   hotels_count = int(user.hotels_count)
  #   filtered_list = []
  #   try:
  #     a = 0
  #     for hotel_obj in list_to_filter:
  #       a += 1
  #       hotel_distance_str = list(filter(lambda elem: elem['label'] == 'Центр города'
  #                                                                or elem['label'] == 'City center',
  #                                                        [elem for elem in hotel_obj['landmarks']]))[0]['distance']
  #       hotel_distance = hotel_distance_str.split(' ')[0].replace(',', '.')
  #       print(a, float(hotel_distance))
  #       if float(user.distance_from_center_min) <= float(hotel_distance) >= float(user.distance_from_center_max):
  #         filtered_list.append(hotel_obj)
  #         if len(filtered_list) == hotels_count:
  #           break
  #   except (KeyError, ValueError, TypeError) as err:
  #     print(err)
  #   finally:
  #     return filtered_list
  else:
    return []

def get_data_from_response(response: Union[Dict], user: 'User') -> List:

  """Функция для извлечения всей необходимой информации об отеле из ответа API
  и для формирования объекта отеля с необходимыми для вывода пользователя данными"""

  result_to_return = []
  if not response.values():
    return result_to_return
  try:
    hotels_list_to_filter = response['data']['body']['searchResults']['results']
    hotels_list = filter_hotels(hotels_list_to_filter, user)
    for hotel_obj in hotels_list:
      hotel_id = hotel_obj['id']

      hotel = dict()
      hotel['id'] = hotel_id
      hotel['name'] = hotel_obj['name']
      hotel['address'] = hotel_obj['address']['streetAddress']
      # hotel['link'] = f'https://www.hotels.com/h{hotel_id}.Hotel-Information'
      hotel['link'] = f'https://www.hotels.com/ho{hotel_id}'
      hotel['distance_from_center'] = list(filter(lambda elem: elem['label'] == 'Центр города'
                                                               or elem['label'] == 'City center',
                                                       [elem for elem in hotel_obj['landmarks']]))[0]['distance']
      price_obj = hotel_obj['ratePlan']['price']
      hotel['price'] = price_obj['current'] #exactCurrent
      # hotel['price_total'] = price_obj['fullyBundledPricePerStay'] if price_obj.get('fullyBundledPricePerStay') \
      #   else price_obj['current']
      total_days = (user.check_out - user.check_in).days
      total_sum = total_days * price_obj['exactCurrent']
      hotel['price_total'] = '${count}'.format(count=round(total_sum, 2)) if total_days > 1 else hotel['price']

      if user.load_image:
        detail = {}
        try:
          detail = fetch_hotel_detail(hotel_id, user)
        except NoneTypeError as err:
          print(err)
        finally:
          target_content_obj = detail['hotelImages']
          hotel['photos'] = get_necessary_img_count(target_content_obj,
                                                    user.load_image, user.load_image_count)
      else:
        hotel['photos'] = []
      result_to_return.append(hotel)


  except (KeyError, IndexError) as err:
    print(err)
    raise NoneTypeError('Разработчики rapidApi изменили ключи')
  except (TypeError) as err:
    print(err)
    return result_to_return
  else:
    return result_to_return

def fetch_result_by_command(user: 'User') -> List:
  """Функция для запроса от API отелей по названию команды, хранящейся в объекте User"""
  url = 'https://hotels4.p.rapidapi.com/properties/list'

  """Если город не найден, выкидываем ошибку на вывод"""
  destination_id = None
  try:
    destination_id = fetch_destination_id(user.city, user.lang)
    if not destination_id:
      raise IncorrectCity('Город указан некорректно.\n'
                          'Возможно, он был удален из системы' if user.lang == 'ru_RU' else 'Your '
                                                                                            'destination is incorrect')
  except ServerSilence as err:
    raise ServerSilence('Сервер не отвечает. '
                        'Попробуйте повторить попытку позднее' if user.lang == 'ru_RU' else 'Server is unavailable. '
                                                                                            'Try again later!!!')

  today = datetime.date.today() if not user.check_in else user.check_in
  tomorrow = today + datetime.timedelta(days=1) if not user.check_out else user.check_out
  check_in = today.strftime('%Y-%m-%d')
  check_out = tomorrow.strftime('%Y-%m-%d')

  querystring_to_validate = {
    'destinationId': f'{destination_id}',
    'pageNumber': '1',
    'pageSize': f'{user.hotels_count}',
    'checkIn': f'{check_in}',
    'checkOut': f'{check_out}',
    'adults1': '2',
    'locale': f'{user.lang}',
    # 'currency': 'RUB' if user.lang == 'ru_RU' else 'USD'
    'currency': 'USD'
  }

  if user.command == 'lowprice':
    querystring_to_validate['sortOrder'] = 'PRICE'
  elif user.command == 'highprice':
    querystring_to_validate['sortOrder'] = 'PRICE_HIGHEST_FIRST'
  elif user.command == 'bestdeal':
    querystring_to_validate['sortOrder'] = 'DISTANCE_FROM_LANDMARK'
    querystring_to_validate['priceMin'] = user.price_min
    querystring_to_validate['priceMax'] = user.price_max
    querystring_to_validate['landmarkIds'] = 'Центр города' if user.lang == 'ru_RU' else 'City center'
    # querystring_to_validate['pageSize'] = '25'
  """Выкидываем на вывод ошибку, если отелей не найдено или сервер долго отвечает"""
  res = {}
  try:
    res = fetch_rapid_api('GET', url, querystring_to_validate) #res: Dict можеть быть пустым
    if not res.get('data'):
      raise NoneTypeError('По переданным параметрам '
                          'отелей не найдено' if user.lang == 'ru_RU' else 'No hotels found '
                                                                           'for the given parameters')
  except ServerSilence as err:
    raise ServerSilence('Сервер не отвечает. '
                        'Попробуйте повторить попытку позднее' if user.lang == 'ru_RU' else 'Server is unavailable. '
                                                                           'Try again later')

  try:
    return get_data_from_response(res, user)
  except (NoneTypeError, KeyError, ValueError, TypeError) as err:
    print(err)
    raise NoneTypeError('Произошла ошибка:( Программисты уже разбираются с этим')
