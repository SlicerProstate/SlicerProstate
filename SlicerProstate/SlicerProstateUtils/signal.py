""" This decorator can be used for creating signals and connecting slots to them. You could compare it to qt signals.
    
    Usage:
    
      class MyClass(SignalProviderBase):
        @signal
        def processingFinished(self):
          pass

        def __init__(self):
          SignalProviderBase.__init__(self)


      class MyListeningClass(object):

        def __init__(self):
          self.myClassInstance = MyClass()
          self.myClassInstance.processingFinished.connect(self.onProcessingFinished)

        def onProcessingFinished(self):
          print "Slot in class: Signal successfully caught. Processing is done!"

      def slot():
        print "Signal successfully caught. Processing is done!"


      myClassInstance = MyClass()
      myClassInstance.processingFinished.connect(slot)

      myClassInstance.processingFinished()

      myListeningClass = MyListeningClass()
      myListeningClass.myClassInstance.processingFinished()

"""


def signal(func):
  func.isSignal = True
  return func


class Signal(object):

  def __init__(self, func):
    self.func = func
    self.slots = []

  def __del__(self):
    self.slots = []

  def __call__(self, *args, **kwargs):
    for slot in self.slots:
      slot(*args[1:])
    return self.func(*args[1:], **kwargs)

  def connect(self, slot):
    if slot not in self.slots:
      self.slots.append(slot)

  def disconnect(self, slot):
    if slot in self.slots:
      self.slots.remove(slot)


class SignalProviderBase(object):

  def __getAllMethods(self):
    return [getattr(self, method) for method in dir(self) if callable(getattr(self, method))]

  def __init__(self):
    for signal in [method for method in self.__getAllMethods() if hasattr(method, "isSignal")]:
      setattr(self, signal.__name__, Signal(signal))
