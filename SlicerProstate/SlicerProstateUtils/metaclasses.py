

class Singleton(type):
  # source: http://amir.rachum.com/blog/2012/04/26/implementing-the-singleton-pattern-in-python/

  def __call__(cls, *args, **kwargs):
    try:
      return cls.__instance
    except AttributeError:
      cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
      return cls.__instance