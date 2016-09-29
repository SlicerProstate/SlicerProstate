from functools import wraps
import itertools
import logging
import inspect
import slicer


class logmethod(object):
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

  def __init__(self, level=logging.DEBUG):
    self.logLevel = level

  def __call__(self, func):
    def wrapped_f(*args, **kwargs):
      args_map = {}
      try:
        if args or kwargs:
          args_map = inspect.getcallargs(func, *args, **kwargs)
      except TypeError:
        pass
      className = ""
      if 'self' in args_map:
        cls = args_map['self'].__class__
        className = cls.__name__ + '.'
      try:
        callerMethod = inspect.stack()[1][0].f_code.co_name
        callerClass = inspect.stack()[1][0].f_locals["self"].__class__.__name__
      except (KeyError, IndexError):
        callerClass = ""
        callerMethod = ""
      caller = ""
      if callerClass != "" and callerMethod != "":
        caller = " from {}.{}".format(callerClass, callerMethod)
      logging.log(self.logLevel, "Called {}{}{} with args {} and kwargs {}".format(className, func.__name__,
                                                                                   caller, args, kwargs))
      return func(*args, **kwargs)
    return wrapped_f


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


class MultiMethodRegistrations(object):

  registry = {}


class MultiMethod(object):
  # source: http://www.artima.com/weblogs/viewpost.jsp?thread=101605
  def __init__(self, name):
    self.__name__ = name
    self.name = name
    self.typemap = {}

  def __call__(self, *args, **kwargs):
    types = tuple(arg.__class__ for arg in args) # a generator expression!
    function = self.typemap.get(types)
    if function is None:
      raise TypeError("no match for types %s" % str(types))
    return function(*args)
  def register(self, types, function):
    if types in self.typemap:
      raise TypeError("duplicate registration")
    self.typemap[types] = function


def multimethod(*types):
  """ This decorator can be used to define different versions of a
      method/function for different datatypes but keeping the same name

      original source: http://www.artima.com/weblogs/viewpost.jsp?thread=101605

      @multimethod([int, float], [int, float], str)
      def foo(arg1, arg2, arg3):
        print arg1, arg2, arg3

      @multimethod([int, float], str)
      def foo(arg1, arg2, arg3):
        print arg1, arg2, arg3

      foo(1,2,"bar")
      foo(1.0,2,"bar")
      foo(1,2.0,"bar")
      foo(1.0,2.0,"bar")
  """

  def register(func):
    name = func.__name__
    mm = MultiMethodRegistrations.registry.get(name)
    if mm is None:
      mm = MultiMethodRegistrations.registry[name] = MultiMethod(name)
    for combination in list(itertools.product(*[[t] if type(t) is not list else t for t in types], repeat=1)):
      mm.register(combination, func)
    return mm
  return register