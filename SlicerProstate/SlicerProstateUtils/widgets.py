import qt, vtk, slicer
import os, sys


class CustomStatusProgressbar(qt.QWidget):

  STYLE = "QWidget{background-color:#FFFFFF;}"

  @property
  def text(self):
    return self.textLabel.text

  @text.setter
  def text(self, value):
    self.textLabel.text = value

  @property
  def value(self):
    return self.progress.value

  @value.setter
  def value(self, value):
    self.progress.value = value
    self.refreshProgressVisibility()

  @property
  def maximum(self):
    return self.progress.maximum

  @maximum.setter
  def maximum(self, value):
    self.progress.maximum = value
    self.refreshProgressVisibility()

  def __init__(self, parent=None, **kwargs):
    qt.QWidget.__init__(self, parent, **kwargs)
    self.setup()

  def setup(self):
    self.textLabel = qt.QLabel()
    self.progress = qt.QProgressBar()
    self.maximumHeight = slicer.util.mainWindow().statusBar().height
    rowLayout = qt.QHBoxLayout()
    self.setLayout(rowLayout)
    rowLayout.addWidget(self.textLabel, 1)
    rowLayout.addWidget(self.progress, 1)
    self.setStyleSheet(self.STYLE)
    self.refreshProgressVisibility()

  def updateStatus(self, text, value=None):
    self.text = text
    if value is not None:
      self.value = value

  def reset(self):
    self.text = ""
    self.progress.reset()
    self.progress.maximum = 100
    self.refreshProgressVisibility()

  def refreshProgressVisibility(self):
    self.progress.visible = self.value > 0 and self.progress.maximum > 0 or self.progress.maximum == 0


class WindowLevelEffectsButton(qt.QPushButton):

  def __init__(self, title, sliceWidgets=None, parent=None, **kwargs):
    qt.QPushButton.__init__(self, title, parent, **kwargs)
    self.wlEffects = {}
    self.setup(sliceWidgets)

  def __del__(self):
    qt.QPushButton.__del__()
    self._disconnectSignals()

  def setup(self, sliceWidgets):
    lm = slicer.app.layoutManager()
    if not sliceWidgets:
      sliceWidgets = []
      sliceLogics = lm.mrmlSliceLogics()
      for n in range(sliceLogics.GetNumberOfItems()):
        sliceLogic = sliceLogics.GetItemAsObject(n)
        sliceWidgets.append(lm.sliceWidget(sliceLogic.GetName()))
    for sliceWidget in sliceWidgets:
      self.wlEffects[sliceWidget] = WindowLevelEffect(sliceWidget)
    self._connectSignals()

  def _connectSignals(self):
    self.connect('toggled(bool)', self._onToggled)

  def _disconnectSignals(self):
    self.disconnect('toggled(bool)', self._onToggled)

  def addSliceWidget(self, sliceWidget):
    if not self.wlEffects.has_key(sliceWidget):
      self.wlEffects[sliceWidget] = WindowLevelEffect(sliceWidget)

  def removeSliceWidget(self, sliceWidget):
    if self.wlEffects.has_key(sliceWidget):
      self.wlEffects[sliceWidget].disable()
      del self.wlEffects[sliceWidget]

  def _onToggled(self, toggled):
    if toggled:
      self._enableWindowLevelEffects()
    else:
      self._disableWindowLevelEffects()

  def _enableWindowLevelEffects(self):
    for wlEffect in self.wlEffects.values():
      wlEffect.enable()

  def _disableWindowLevelEffects(self):
    for wlEffect in self.wlEffects.values():
      wlEffect.disable()


class WindowLevelEffect(object):

  EVENTS = [vtk.vtkCommand.LeftButtonPressEvent,
            vtk.vtkCommand.LeftButtonReleaseEvent,
            vtk.vtkCommand.MouseMoveEvent]

  def __init__(self, sliceWidget):
    self.actionState = None
    self.startXYPosition = None
    self.currentXYPosition = None
    self.cursor = self.createWLCursor()

    self.sliceWidget = sliceWidget
    self.sliceLogic = sliceWidget.sliceLogic()
    self.compositeNode = sliceWidget.mrmlSliceCompositeNode()
    self.sliceView = self.sliceWidget.sliceView()
    self.interactor = self.sliceView.interactorStyle().GetInteractor()

    self.actionState = None

    self.interactorObserverTags = []

    self.bgStartWindowLevel = [0,0]
    self.fgStartWindowLevel = [0,0]

  def createWLCursor(self):
    iconPath = os.path.join(os.path.dirname(sys.modules[self.__module__].__file__),
                            '../Resources/Icons/cursor-window-level.png')
    pixmap = qt.QPixmap(iconPath)
    return qt.QCursor(qt.QIcon(pixmap).pixmap(32, 32), 0, 0)

  def enable(self):
    for e in self.EVENTS:
      tag = self.interactor.AddObserver(e, self.processEvent, 1.0)
      self.interactorObserverTags.append(tag)

  def disable(self):
    for tag in self.interactorObserverTags:
      self.interactor.RemoveObserver(tag)
    self.interactorObserverTags = []

  def processEvent(self, caller=None, event=None):
    """
    handle events from the render window interactor
    """
    bgLayer = self.sliceLogic.GetBackgroundLayer()
    fgLayer = self.sliceLogic.GetForegroundLayer()

    bgNode = bgLayer.GetVolumeNode()
    fgNode = fgLayer.GetVolumeNode()

    changeFg = 1 if fgNode and self.compositeNode.GetForegroundOpacity() > 0.5 else 0
    changeBg = not changeFg

    if event == "LeftButtonPressEvent":
      self.actionState = "dragging"
      self.sliceWidget.setCursor(self.cursor)

      xy = self.interactor.GetEventPosition()
      self.startXYPosition = xy
      self.currentXYPosition = xy

      if bgNode:
        bgDisplay = bgNode.GetDisplayNode()
        self.bgStartWindowLevel = [bgDisplay.GetWindow(), bgDisplay.GetLevel()]
      if fgNode:
        fgDisplay = fgNode.GetDisplayNode()
        self.fgStartWindowLevel = [fgDisplay.GetWindow(), fgDisplay.GetLevel()]
      self.abortEvent(event)

    elif event == "MouseMoveEvent":
      if self.actionState == "dragging":
        if bgNode and changeBg:
          self.updateNodeWL(bgNode, self.bgStartWindowLevel, self.startXYPosition)
        if fgNode and changeFg:
          self.updateNodeWL(fgNode, self.fgStartWindowLevel, self.startXYPosition)
        self.abortEvent(event)

    elif event == "LeftButtonReleaseEvent":
      self.sliceWidget.unsetCursor()
      self.actionState = ""
      self.abortEvent(event)

  def updateNodeWL(self, node, startWindowLevel, startXY):

    currentXY = self.interactor.GetEventPosition()

    vDisplay = node.GetDisplayNode()
    vImage = node.GetImageData()
    vRange = vImage.GetScalarRange()

    deltaX = currentXY[0]-startXY[0]
    deltaY = currentXY[1]-startXY[1]
    gain = (vRange[1]-vRange[0])/500.
    newWindow = startWindowLevel[0]+(gain*deltaX)
    newLevel = startWindowLevel[1]+(gain*deltaY)

    vDisplay.SetAutoWindowLevel(0)
    vDisplay.SetWindowLevel(newWindow, newLevel)
    vDisplay.Modified()

  def abortEvent(self, event):
    """Set the AbortFlag on the vtkCommand associated
    with the event - causes other things listening to the
    interactor not to receive the events"""
    # TODO: make interactorObserverTags a map to we can
    # explicitly abort just the event we handled - it will
    # be slightly more efficient
    for tag in self.interactorObserverTags:
      cmd = self.interactor.GetCommand(tag)
      cmd.SetAbortFlag(1)