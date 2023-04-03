from typing import Any, Union, Optional
from .config import BOT_VARIABLES
from datetime import date, timedelta

hotels_max_count_output = BOT_VARIABLES['hotels_max_count_output']
bot_commands_list = BOT_VARIABLES['bot_commands_list']

class User:
  users = dict()

  def __init__(self, user_id) -> None:
    self._lang = 'en_EN'
    self._city = None
    self._check_in = None
    self._check_out = None
    self._hotels_count = 0
    self._load_image = False
    self._load_image_count = 0
    self._price_min = None
    self._price_max = None
    self._distance_from_center_min = None
    self._distance_from_center_max = None
    self._command = None
    User.add_user(user_id, self)

  @property
  def lang(self) -> str:
    return self._lang

  @lang.setter
  def lang(self, lang: str) -> None:
    if lang == 'ru':
      self._lang = 'ru_RU'
    else:
      self._lang = 'en_EN'

  @property
  def city(self) -> Optional[str]:
    return self._city

  @city.setter
  def city(self, city: str) -> None:
    self._city = self._check_str_param(city).lower()

  @property
  def check_in(self) -> Optional[date]:
    return self._check_in

  @check_in.setter
  def check_in(self, check_in: date) -> None:
    if isinstance(check_in, date):
      self._check_in = check_in
    else:
      self._check_in = None

  @property
  def check_out(self) -> Optional[date]:
    return self._check_out

  @check_out.setter
  def check_out(self, check_out: date) -> None:
    if isinstance(check_out, date):
      self._check_out = check_out
    else:
      self._check_out = None

  @property
  def hotels_count(self) -> int:
    return self._hotels_count

  @hotels_count.setter
  def hotels_count(self, count: Union[int, float, str]) -> None:
    count_to_set = self._check_int_param(param=count, default=1)
    if 0 < count_to_set <= hotels_max_count_output:
      self._hotels_count = count_to_set
    else:
      self._hotels_count = hotels_max_count_output

  @property
  def load_image(self) -> bool:
    return self._load_image

  @load_image.setter
  def load_image(self, is_load: bool) -> None:
    self._load_image = self._check_bool_param(is_load)

  @property
  def load_image_count(self) -> int:
    return self._load_image_count

  @load_image_count.setter
  def load_image_count(self, count: Union[int, float, str]) -> None:
    max_count = int(hotels_max_count_output / 2)
    count_to_set = self._check_int_param(param=count, default=1)
    if 0 < count_to_set <= max_count:
      self._load_image_count = count_to_set
    elif count_to_set <= 0:
      self._load_image = False
      self._load_image_count = 0
    else:
      self._load_image_count = max_count

  @property
  def price_min(self) -> Optional[int]:
    return self._price_min

  @price_min.setter
  def price_min(self, price: Union[int, float, str]) -> None:
    self._price_min = self._check_int_param(param=price, default=0)

  @property
  def price_max(self) -> Optional[int]:
    return self._price_max

  @price_max.setter
  def price_max(self, price: Union[int, float, str]) -> None:
    self._price_max = self._check_int_param(param=price, default=10000)

  @property
  def distance_from_center_min(self) -> Optional[int]:
    return self._distance_from_center_min

  @distance_from_center_min.setter
  def distance_from_center_min(self, distance: Union[int, float, str]) -> None:
    self._distance_from_center_min = self._check_int_param(param=distance, default=0)

  @property
  def distance_from_center_max(self) -> Optional[int]:
    return self._distance_from_center_max

  @distance_from_center_max.setter
  def distance_from_center_max(self, distance: Union[int, float, str]) -> None:
    self._distance_from_center_max = self._check_int_param(param=distance, default=0)

  @property
  def command(self) -> Optional[str]:
    return self._command

  @command.setter
  def command(self, command: str) -> None:
    if command in bot_commands_list:
      self._command = self._check_str_param(command).lower()
    else: self._command = None

  @classmethod
  def get_user(cls, user_id: Union[int, str]) -> 'User':
    to_get_id = f'{user_id}'
    if cls.users.get(to_get_id) is None:
      new_user = User(to_get_id)
      return new_user
    return User.users.get(to_get_id)

  @classmethod
  def add_user(cls, user_id: Union[int, str], user: 'User') -> None:
    cls.users[f'{user_id}'] = user

  @staticmethod
  def _check_str_param(param: Union[int, float, str]) -> str:
    if type(param) is not str:
      return f'{param}'
    return param

  @staticmethod
  def _check_int_param(param: Union[int, float, str], default: int) -> int:
    output_param = param
    if type(param) is not int:
      try:
        output_param = int(param)
      except ValueError:
        output_param = default
    return output_param

  @staticmethod
  def _check_bool_param(param: Any) -> bool:
    if type(param) is not bool:
      return bool(param)
    return param
