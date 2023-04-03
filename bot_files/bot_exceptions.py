class NoneTypeError(Exception):
  def __init__(self, *args):
    if args:
      self.message = f'{args[0]}'
    else:
      self.message = None

  def __str__(self):
    if self.message:
      return self.message
    else:
      return 'NoneTypeError has been raised'



class IncorrectCity(Exception):
  def __init__(self, *args):
    if args:
      self.message = f'{args[0]}'
    else:
      self.message = None

  def __str__(self):
    if self.message:
      return self.message
    else:
      return 'Your destination is incorrect'

class ServerSilence(Exception):
  def __init__(self, *args):
    if args:
      self.message = f'{args[0]}'
    else:
      self.message = None

  def __str__(self):
    if self.message:
      return self.message
    else:
      return 'Server is unavailable. Try again later'