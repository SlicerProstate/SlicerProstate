from functools import wraps
import logging
import inspect
import slicer


def logmethod(level=logging.DEBUG):
  """ This decorator can used for logging methods without the need of reimplementing log messages again and again. The
      decorator logs information about the called method name including caller and arguments

    Usage:

    @logmethod()
    def sub(x,y, switch=False):
      return x -y if not switch else y-x

    @logmethod(level=logging.INFO)
    def sub(x,y, switch=False):
      return x -y if not switch else y-x
  """

  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      args_map = {}
      if args or kwargs:
        args_map = inspect.getcallargs(func, *args, **kwargs)
      className = ""
      if 'self' in args_map:
        cls = args_map['self'].__class__
        className = cls.__name__+'.'
      try:
        callerMethod = inspect.stack()[1][0].f_code.co_name
        callerClass = inspect.stack()[1][0].f_locals["self"].__class__.__name__
      except (KeyError, IndexError):
        callerClass = ""
        callerMethod = ""
      caller = ""
      if callerClass != "" and callerMethod != "":
        caller = " from {}.{}".format(callerClass, callerMethod)
      logging.log(level, "Called {}{}{} with args {} and kwargs {}".format(className, func.__name__,
                                                                                    caller, args, kwargs))

      return func(*args, **kwargs)
    return wrapper
  return decorator


def onExceptionReturnNone(func):

  @wraps(func)
  def wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except (IndexError, AttributeError, KeyError):
      return None
  return wrapper


def onReturnProcessEvents(func):

  @wraps(func)
  def wrapper(*args, **kwargs):
    func(*args, **kwargs)
    slicer.app.processEvents()
  return wrapper


def beforeRunProcessEvents(func):

  @wraps(func)
  def wrapper(*args, **kwargs):
    slicer.app.processEvents()
    func(*args, **kwargs)
  return wrapper


def callCount(level=logging.DEBUG):

  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      args_map = {}
      if args or kwargs:
        args_map = inspect.getcallargs(func, *args, **kwargs)
      className = ""
      if 'self' in args_map:
        cls = args_map['self'].__class__
        className = cls.__name__ + '.'
      wrapper.count += 1
      logging.log(level, "{}{} called {} times".format(className, func.__name__, wrapper.count))
      return func(*args, **kwargs)

    wrapper.count = 0
    return wrapper
  return decorator