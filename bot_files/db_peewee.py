from typing import List
from peewee import *
from datetime import datetime
from .config import BOT_VARIABLES

db = SqliteDatabase('history.db')


class Call(Model):
  chat_id = IntegerField()
  command = CharField()
  call_date = DateTimeField(default=datetime.now)
  city = CharField()

  class Meta:
    database = db
    db_table = 'calls'
    order_by = 'call_date'

class Result(Model):
  call = ForeignKeyField(Call, related_name='results')
  hotel_name = CharField()
  hotel_url = CharField()

  class Meta:
    database = db
    db_table = 'results'

def get_calls_history(chat_id: int, limit: int = BOT_VARIABLES['history_max_count_commands']) -> List:
  calls = Call.select().where((Call.chat_id == chat_id)).order_by(Call.call_date.desc()).limit(limit)
  commands = []
  for call in calls:
    command = {}
    command['command_name'] = call.command
    command['city'] = call.city
    date = call.call_date
    command['date'] = '{day}.{month}.{year}  ⏰ ' \
                      '{hour}:{minute}'.format(minute=date.minute if date.minute > 9 else '0{m}'.format(m=date.minute),
                                               day=date.day, month=date.month, year=date.year, hour=date.hour)
    hotels = []
    for hotel in call.results:
      hotel_obj = {}
      hotel_obj['hotel_name'] = hotel.hotel_name
      hotel_obj['hotel_url'] = hotel.hotel_url
      hotels.append(hotel_obj)
    command['hotels'] = hotels
    commands.append(command)
  return commands

def create_table():
  Call.create_table()
  Result.create_table()


