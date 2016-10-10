import qt, vtk, slicer
import inspect, os, sys
from events import SlicerProstateEvents
from mixins import ParameterNodeObservationMixin
from decorators import logmethod


class BasicIconButton(qt.QPushButton):

  FILE_NAME=None

  @property
  def buttonIcon(self):
    if not self.FILE_NAME:
      return None
    iconPath = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), '../Resources/Icons', self.FILE_NAME)
    pixmap = qt.QPixmap(iconPath)
    return qt.QIcon(pixmap)

  def __init__(self, title="", parent=None, **kwargs):
    qt.QPushButton.__init__(self, title, parent, **kwargs)
    self.setIcon(self.buttonIcon)
    self._connectSignals()

  def _connectSignals(self):
    self.destroyed.connect(self.onAboutToBeDestroyed)

  def onAboutToBeDestroyed(self, obj):
    obj.destroyed.disconnect(self.onAboutToBeDestroyed)


class LayoutButton(BasicIconButton):

  LAYOUT=None

  @property
  def layoutManager(self):
    return slicer.app.layoutManager()

  def __init__(self, title="", parent=None, **kwargs):
    super(LayoutButton, self).__init__(title, parent, **kwargs)
    self.checkable = True
    if not self.LAYOUT:
      raise NotImplementedError("Member variable LAYOUT needs to be defined by all deriving classes")
    self.onLayoutChanged(self.layoutManager.layout)

  def _connectSignals(self):
    super(LayoutButton, self)._connectSignals()
    self.toggled.connect(self.onToggled)
    self.layoutManager.layoutChanged.connect(self.onLayoutChanged)

  def onAboutToBeDestroyed(self, obj):
    super(LayoutButton, self).onAboutToBeDestroyed(obj)
    if self.layoutManager:
      self.layoutManager.layoutChanged.disconnect(self.onLayoutChanged)

  def onLayoutChanged(self, layout):
    self.checked = self.LAYOUT == layout

  def onToggled(self, checked):
    if checked and self.layoutManager.layout != self.LAYOUT:
      self.layoutManager.setLayout(self.LAYOUT)
    if not checked and self.LAYOUT == self.layoutManager.layout:
      self.onLayoutChanged(self.LAYOUT)


class RedSliceLayoutButton(LayoutButton):

  FILE_NAME = 'LayoutOneUpRedSliceView.png'
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView

  def __init__(self, title="", parent=None, **kwargs):
    super(RedSliceLayoutButton, self).__init__(title, parent, **kwargs)
    self.toolTip = "Red Slice Only Layout"


class FourUpLayoutButton(LayoutButton):

  FILE_NAME = 'LayoutFourUpView.png'
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView

  def __init__(self, title="", parent=None, **kwargs):
    super(FourUpLayoutButton, self).__init__(title, parent, **kwargs)
    self.toolTip = "Four-Up Layout"


class FourUpTableViewLayoutButton(LayoutButton):

  FILE_NAME = 'LayoutFourUpTableView.png'
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView

  def __init__(self, title="", parent=None, **kwargs):
    super(FourUpTableViewLayoutButton, self).__init__(title, parent, **kwargs)
    self.toolTip = "Four-Up Table Layout"


class SideBySideLayoutButton(LayoutButton):

  FILE_NAME = 'LayoutSideBySideView.png'
  LAYOUT = slicer.vtkMRMLLayoutNode.SlicerLayoutSideBySideView

  def __init__(self, title="", parent=None, **kwargs):
    super(SideBySideLayoutButton, self).__init__(title, parent, **kwargs)
    self.toolTip = "Side by Side Layout"


class CheckableIconButton(BasicIconButton):

  def __init__(self, title="", parent=None, **kwargs):
    BasicIconButton.__init__(self, title, parent, **kwargs)
    self.checkable = True

  def _connectSignals(self):
    super(CheckableIconButton, self)._connectSignals()
    self.toggled.connect(self.onToggled)

  def onToggled(self, checked):
    raise NotImplementedError()


class CrosshairButton(CheckableIconButton, ParameterNodeObservationMixin):

  FILE_NAME = 'SlicesCrosshair.png'
  CursorPositionModifiedEvent = SlicerProstateEvents.CursorPositionModifiedEvent

  def __init__(self, title="", parent=None, **kwargs):
    super(CrosshairButton, self).__init__(title, parent, **kwargs)
    self.toolTip = "Show crosshair"
    self.crosshairNodeObserverTag = None
    self.crosshairNode = slicer.mrmlScene.GetNthNodeByClass(0, 'vtkMRMLCrosshairNode')
    self.connectCrosshairNode()

  def onAboutToBeDestroyed(self, obj):
    super(CrosshairButton, self).onAboutToBeDestroyed(obj)
    self.disconnectCrosshairNode()

  def connectCrosshairNode(self):
    if not self.crosshairNodeObserverTag:
      self.crosshairNodeObserverTag = self.crosshairNode.AddObserver(self.CursorPositionModifiedEvent,
                                                                     self.onCursorPositionChanged)

  def disconnectCrosshairNode(self):
    if self.crosshairNode and self.crosshairNodeObserverTag:
      self.crosshairNode.RemoveObserver(self.crosshairNodeObserverTag)
    self.crosshairNodeObserverTag = None

  def onCursorPositionChanged(self, observee=None, event=None):
    self.invokeEvent(self.CursorPositionModifiedEvent, self.crosshairNode)

  def onToggled(self, checked):
      self.crosshairNode.SetCrosshairMode(slicer.vtkMRMLCrosshairNode.ShowSmallBasic if checked
                                          else slicer.vtkMRMLCrosshairNode.NoCrosshair)


class WindowLevelEffectsButton(CheckableIconButton):

  FILE_NAME = 'icon-WindowLevelEffect.png'

  @property
  def sliceWidgets(self):
    return self._sliceWidgets

  @sliceWidgets.setter
  def sliceWidgets(self, value):
    self._sliceWidgets = value
    self.setup()

  def __init__(self, title="", sliceWidgets=None, parent=None, **kwargs):
    super(WindowLevelEffectsButton, self).__init__(title, parent, **kwargs)
    self.toolTip = "Change W/L with respect to FG and BG opacity"
    self.wlEffects = {}
    self.sliceWidgets = sliceWidgets

  def refreshForAllAvailableSliceWidgets(self):
    self.sliceWidgets = None

  def setup(self):
    lm = slicer.app.layoutManager()
    if not self.sliceWidgets:
      self._sliceWidgets = []
      sliceLogics = lm.mrmlSliceLogics()
      for n in range(sliceLogics.GetNumberOfItems()):
        sliceLogic = sliceLogics.GetItemAsObject(n)
        self._sliceWidgets.append(lm.sliceWidget(sliceLogic.GetName()))
    for sliceWidget in self._sliceWidgets :
      self.addSliceWidget(sliceWidget)

  def cleanupSliceWidgets(self):
    for sliceWidget in self.wlEffects.keys():
      if sliceWidget not in self._sliceWidgets:
        self.removeSliceWidget(sliceWidget)

  def addSliceWidget(self, sliceWidget):
    if not self.wlEffects.has_key(sliceWidget):
      self.wlEffects[sliceWidget] = WindowLevelEffect(sliceWidget)

  def removeSliceWidget(self, sliceWidget):
    if self.wlEffects.has_key(sliceWidget):
      self.wlEffects[sliceWidget].disable()
      del self.wlEffects[sliceWidget]

  def onToggled(self, checked):
    self._enableWindowLevelEffects() if checked else self._disableWindowLevelEffects()


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