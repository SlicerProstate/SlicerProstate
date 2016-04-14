import DICOMLib
import os, sys
import slicer, vtk, ctk, qt
import xml.dom.minidom, datetime
from constants import DICOMTAGS
from mixins import ModuleLogicMixin, ModuleWidgetMixin


class SmartDICOMReceiver(ModuleLogicMixin):

  STATUS_RECEIVING = "Receiving DICOM data"
  STATUS_WAITING = "Waiting for incoming DICOM data"
  STATUS_COMPLETED = "DICOM data receive completed."

  def __init__(self, incomingDataDirectory, receiveFinishedCallback, statusCallback=None):
    self.incomingDataDirectory = incomingDataDirectory
    self.receiveFinishedCallback = receiveFinishedCallback
    self.statusCallback = slicer.util.showStatusMessage if not statusCallback else statusCallback
    self.storeSCPProcess = None
    self.setupTimers()
    self.reset()

  def reset(self):
    self.timerIterations = 0
    self.startingFileList = []
    self.currentFileList = []
    self.dataHasBeenReceived = False

  def setupTimers(self):
    self.dataReceivedTimer = self.createTimer(interval=5000, slot=self.checkIfStillSameFileCount, singleShot=True)
    self.watchTimer = self.createTimer(interval=1000, slot=self.startWatching, singleShot=True)

  def start(self, showDots=True):
    self.showDots = showDots
    self.stop()

    self.startingFileList = self.getFileList(self.incomingDataDirectory)
    self.lastFileCount = len(self.startingFileList)

    self.storeSCPProcess = DICOMLib.DICOMStoreSCPProcess(incomingDataDir=self.incomingDataDirectory)
    self.startWatching()
    self.storeSCPProcess.start()

  def stop(self):
    self.stopWatching()
    if self.storeSCPProcess:
      self.storeSCPProcess.stop()
    self.reset()

  def startWatching(self):
    self.currentFileList = self.getFileList(self.incomingDataDirectory)
    if self.lastFileCount != len(self.currentFileList):
      status = self.getReceivingStatusMessage(self.STATUS_RECEIVING) if self.showDots else self.STATUS_RECEIVING
      self.statusCallback(status)
      self.dataHasBeenReceived = True
      self.lastFileCount = len(self.currentFileList)
      self.watchTimer.start()
    elif self.dataHasBeenReceived:
      self.lastFileCount = len(self.currentFileList)
      self.statusCallback(self.STATUS_COMPLETED)
      self.dataReceivedTimer.start()
    else:
      self.statusCallback(self.STATUS_WAITING)
      self.watchTimer.start()

  def getReceivingStatusMessage(self, message):
    if self.timerIterations == 4:
      self.timerIterations = 0
    dots = ""
    for iteration in range(self.timerIterations):
      dots += "."
    self.timerIterations += 1
    return message + dots

  def stopWatching(self):
    self.dataReceivedTimer.stop()
    self.watchTimer.stop()

  def checkIfStillSameFileCount(self):
    self.currentFileList = self.getFileList(self.incomingDataDirectory)
    if self.lastFileCount == len(self.currentFileList):
      newFileList = list(set(self.currentFileList) - set(self.startingFileList))
      self.startingFileList = self.currentFileList
      self.lastFileCount = len(self.startingFileList)
      self.receiveFinishedCallback(newFileList=newFileList)
    self.watchTimer.start()


class SliceAnnotation(object):

  ALIGN_LEFT = "left"
  ALIGN_CENTER = "center"
  ALIGN_RIGHT = "right"
  ALIGN_TOP = "top"
  ALIGN_BOTTOM = "bottom"
  POSSIBLE_VERTICAL_ALIGN = [ALIGN_TOP, ALIGN_CENTER, ALIGN_BOTTOM]
  POSSIBLE_HORIZONTAL_ALIGN = [ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT]

  @property
  def fontSize(self):
    return self._fontSize

  @fontSize.setter
  def fontSize(self, size):
    self._fontSize = size
    if self.textProperty:
      self.textProperty.SetFontSize(self.fontSize)
      self.textActor.SetTextProperty(self.textProperty)
    self.update()

  @property
  def textProperty(self):
    if not self.textActor:
      return None
    return self.textActor.GetTextProperty()

  @textProperty.setter
  def textProperty(self, textProperty):
    assert issubclass(textProperty, vtk.vtkTextProperty)
    self.textActor.SetTextProperty(textProperty)
    self.update()

  @property
  def opacity(self):
    if self.textProperty:
      return self.textProperty.GetOpacity()
    return None

  @opacity.setter
  def opacity(self, value):
    if not self.textProperty:
      return
    self.textProperty.SetOpacity(value)
    self.update()

  @property
  def color(self):
    if self.textProperty:
      return self.textProperty.GetColor()

  @color.setter
  def color(self, value):
    assert type(value) is tuple and len(value) == 3
    if self.textProperty:
      self.textProperty.SetColor(value)
      self.update()

  @property
  def verticalAlign(self):
    return self._verticalAlign

  @verticalAlign.setter
  def verticalAlign(self, value):
    if value not in self.POSSIBLE_VERTICAL_ALIGN:
      raise ValueError("Value %s is not allowed for vertical alignment. Only the following values are allowed: %s"
                       % (str(value), str(self.POSSIBLE_VERTICAL_ALIGN)))
    else:
      self._verticalAlign = value

  @property
  def horizontalAlign(self):
    return self._horizontalAlign

  @horizontalAlign.setter
  def horizontalAlign(self, value):
    if value not in self.POSSIBLE_HORIZONTAL_ALIGN:
      raise ValueError("Value %s is not allowed for horizontal alignment. Only the following values are allowed: %s"
                       % (str(value), str(self.POSSIBLE_HORIZONTAL_ALIGN)))
    else:
      self._horizontalAlign = value

  @property
  def renderer(self):
    return self.sliceView.renderWindow().GetRenderers().GetItemAsObject(0)

  def __init__(self, widget, text, **kwargs):
    self.observer = None
    self.textActor = None
    self.text = text

    self.sliceWidget = widget
    self.sliceView = widget.sliceView()
    self.sliceLogic = widget.sliceLogic()
    self.sliceNode = self.sliceLogic.GetSliceNode()
    self.sliceNodeDimensions = self.sliceNode.GetDimensions()

    self.xPos = kwargs.pop('xPos', 0)
    self.yPos = kwargs.pop('yPos', 0)

    self.initialFontSize = kwargs.pop('fontSize', 20)
    self.fontSize = self.initialFontSize
    self.textColor = kwargs.pop('color', (1, 0, 0))
    self.textBold = kwargs.pop('bold', 1)
    self.textShadow = kwargs.pop('shadow', 1)
    self.textOpacity = kwargs.pop('opacity', 1.0)
    self.verticalAlign = kwargs.pop('verticalAlign', 'center')
    self.horizontalAlign = kwargs.pop('horizontalAlign', 'center')

    self.createTextActor()

  def show(self):
    self.fitIntoViewport()
    self._addActor()
    self._addObserver()
    self.sliceView.update()

  def hide(self):
    self.remove()

  def remove(self):
    self._removeObserver()
    self._removeActor()
    self.sliceView.update()

  def _addObserver(self):
    if not self.observer and self.sliceNode:
      self.observer = self.sliceNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.modified)

  def _removeObserver(self):
    if self.observer:
      self.sliceNode.RemoveObserver(self.observer)
      self.observer = None

  def _removeActor(self):
    try:
      self.renderer.RemoveActor(self.textActor)
    except:
      pass

  def _addActor(self):
    self.renderer.AddActor(self.textActor)
    self.update()

  def update(self):
    self.sliceView.update()

  def createTextActor(self):
    self.textActor = vtk.vtkTextActor()
    self.textActor.SetInput(self.text)
    self.textProperty.SetFontSize(self.fontSize)
    self.textProperty.SetColor(self.textColor)
    self.textProperty.SetBold(self.textBold)
    self.textProperty.SetShadow(self.textShadow)
    self.textProperty.SetOpacity(self.textOpacity)
    self.textActor.SetTextProperty(self.textProperty)
    self.show()

  def applyPositioning(self):
    xPos = self.applyHorizontalAlign()
    yPos = self.applyVerticalAlign()
    self.textActor.SetDisplayPosition(xPos, yPos)

  def applyHorizontalAlign(self):
    centerX = int((self.sliceView.width - self.getFontWidth()) / 2)
    if self.xPos:
      xPos = self.xPos if 0 < self.xPos < centerX else centerX
    else:
      if self.horizontalAlign == self.ALIGN_LEFT:
        xPos = 0
      elif self.horizontalAlign == self.ALIGN_CENTER:
        xPos = centerX
      elif self.horizontalAlign == self.ALIGN_RIGHT:
        xPos = self.sliceView.width - self.getFontWidth()
    return int(xPos)

  def applyVerticalAlign(self):
    centerY = int((self.sliceView.height - self.getFontHeight()) / 2)
    if self.yPos:
      yPos = self.yPos if 0 < self.yPos < centerY else centerY
    else:
      if self.verticalAlign == self.ALIGN_TOP:
        yPos = self.sliceView.height - self.getFontHeight()
      elif self.verticalAlign == self.ALIGN_CENTER:
        yPos = centerY
      elif self.verticalAlign == self.ALIGN_BOTTOM:
        yPos = 0
    return int(yPos)

  def modified(self, observee, event):
    if event != "ModifiedEvent":
      return
    currentDimensions = observee.GetDimensions()
    if currentDimensions != self.sliceNodeDimensions:
      self.fitIntoViewport()
      self.update()
      self.sliceNodeDimensions = currentDimensions

  def getFontWidth(self):
    return self.getFontDimensions()[0]

  def getFontHeight(self):
    return self.getFontDimensions()[1]

  def getFontDimensions(self):
    size = [0.0, 0.0]
    self.textActor.GetSize(self.renderer, size)
    return size

  def fitIntoViewport(self):
    while self.getFontWidth() < self.sliceView.width and self.fontSize < self.initialFontSize:
      self.fontSize += 1
    while self.getFontWidth() > self.sliceView.width:
      self.fontSize -= 1
    self.applyPositioning()


class ExtendedQMessageBox(qt.QMessageBox):

  def __init__(self, parent= None):
    super(ExtendedQMessageBox, self).__init__(parent)
    self.setupUI()

  def setupUI(self):
    self.checkbox = qt.QCheckBox("Remember the selection and do not notify again")
    self.layout().addWidget(self.checkbox, 1,2)

  def exec_(self, *args, **kwargs):
    return qt.QMessageBox.exec_(self, *args, **kwargs), self.checkbox.isChecked()


class IncomingDataMessageBox(ExtendedQMessageBox):

  def __init__(self, parent=None):
    super(IncomingDataMessageBox, self).__init__(parent)
    self.setWindowTitle("Incoming image data")
    self.setText("New data has been received. What would you do?")
    self.setIcon(qt.QMessageBox.Question)
    trackButton =  self.addButton(qt.QPushButton('Track targets'), qt.QMessageBox.AcceptRole)
    self.addButton(qt.QPushButton('Postpone'), qt.QMessageBox.NoRole)
    self.setDefaultButton(trackButton)


class IncomingDataWindow(qt.QWidget, ModuleWidgetMixin):

  def __init__(self, callback=None, title="Receiving image data", skipText="Skip", cancelText="Cancel", *args):
    super(IncomingDataWindow, self).__init__(*args)
    self.setWindowTitle(title)
    self.callback = callback if callback else None
    self.setWindowFlags(qt.Qt.CustomizeWindowHint | qt.Qt.WindowTitleHint | qt.Qt.WindowStaysOnTopHint)
    self.skipButtonText = skipText
    self.cancelButtonText = cancelText
    self.setup()

  def setText(self, text):
    self.skipButton.enabled = text in SmartDICOMReceiver.STATUS_WAITING
    self.textLabel.text = text

  def show(self, disableWidget=None):
    self.disabledWidget = disableWidget
    if disableWidget:
      disableWidget.enabled = False
    qt.QWidget.show(self)

  def hide(self):
    if self.disabledWidget:
      self.disabledWidget.enabled = True
      self.disabledWidget = None
    qt.QWidget.hide(self)

  def setup(self):
    self.setLayout(qt.QGridLayout())
    self.statusLabel = qt.QLabel("Status:")
    self.textLabel = qt.QLabel()
    self.layout().addWidget(self.statusLabel, 0, 0)
    self.layout().addWidget(self.textLabel, 0, 1)

    self.progress = qt.QProgressBar()
    self.progress.maximum = 0
    self.progress.setAlignment(qt.Qt.AlignCenter)

    self.layout().addWidget(self.progress, 1, 0, 1, qt.QSizePolicy.ExpandFlag)

    self.buttonGroup = qt.QButtonGroup()
    self.skipButton = self.createButton(self.skipButtonText)
    self.cancelButton = self.createButton(self.cancelButtonText)
    self.buttonGroup.addButton(self.skipButton)
    self.buttonGroup.addButton(self.cancelButton)
    self.layout().addWidget(self.skipButton, 2, 0)
    self.layout().addWidget(self.cancelButton, 2, 1)
    self.setupConnections()

  def setupConnections(self):
    self.buttonGroup.connect('buttonClicked(QAbstractButton*)', self.onButtonClicked)

  def onButtonClicked(self, button):
    if self.callback:
      self.callback(button)
    self.hide()


class RatingWindow(qt.QWidget, ModuleWidgetMixin):

  @property
  def maximumValue(self):
    return self._maximumValue

  @maximumValue.setter
  def maximumValue(self, value):
    if value < 1:
      raise ValueError("The maximum rating value cannot be less than 1.")
    else:
      self._maximumValue = value

  def __init__(self, maximumValue, text="Please rate the registration result:", *args):
    qt.QWidget.__init__(self, *args)
    self.maximumValue = maximumValue
    self.text = text
    self.iconPath = os.path.join(os.path.dirname(sys.modules[self.__module__].__file__), '../Resources/Icons')
    self.setupIcons()
    self.setLayout(qt.QGridLayout())
    self.setWindowFlags(qt.Qt.WindowStaysOnTopHint | qt.Qt.FramelessWindowHint)
    self.setupElements()
    self.connectButtons()
    self.showRatingValue = True

  def __del__(self):
    self.disconnectButtons()

  def isRatingEnabled(self):
    return not self.disableWidgetCheckbox.checked

  def setupIcons(self):
    self.filledStarIcon = self.createIcon("icon-star-filled.png", self.iconPath)
    self.unfilledStarIcon = self.createIcon("icon-star-unfilled.png", self.iconPath)

  def show(self, disableWidget=None, callback=None):
    self.disabledWidget = disableWidget
    if disableWidget:
      disableWidget.enabled = False
    qt.QWidget.show(self)
    self.ratingScore = None
    self.callback = callback

  def setupElements(self):
    self.layout().addWidget(qt.QLabel(self.text), 0, 0)
    self.ratingButtonGroup = qt.QButtonGroup()
    for rateValue in range(1, self.maximumValue+1):
      attributeName = "button"+str(rateValue)
      setattr(self, attributeName, self.createButton('', icon=self.unfilledStarIcon))
      self.ratingButtonGroup.addButton(getattr(self, attributeName), rateValue)

    for button in list(self.ratingButtonGroup.buttons()):
      button.setCursor(qt.Qt.PointingHandCursor)

    self.ratingLabel = self.createLabel("")
    row = self.createHLayout(list(self.ratingButtonGroup.buttons()) + [self.ratingLabel])
    self.layout().addWidget(row, 1, 0)

    self.disableWidgetCheckbox = qt.QCheckBox("Don't display this window again")
    self.disableWidgetCheckbox.checked = False
    self.layout().addWidget(self.disableWidgetCheckbox, 2, 0)

  def connectButtons(self):
    self.ratingButtonGroup.connect('buttonClicked(int)', self.onRatingButtonClicked)
    for button in list(self.ratingButtonGroup.buttons()):
      button.installEventFilter(self)

  def disconnectButtons(self):
    self.ratingButtonGroup.disconnect('buttonClicked(int)', self.onRatingButtonClicked)
    for button in list(self.ratingButtonGroup.buttons()):
      button.removeEventFilter(self)

  def eventFilter(self, obj, event):
    if obj in list(self.ratingButtonGroup.buttons()) and event.type() == qt.QEvent.HoverEnter:
      self.onHoverEvent(obj)
    elif obj in list(self.ratingButtonGroup.buttons()) and event.type() == qt.QEvent.HoverLeave:
      self.onLeaveEvent()
    return qt.QWidget.eventFilter(self, obj, event)

  def onLeaveEvent(self):
    for button in list(self.ratingButtonGroup.buttons()):
      button.icon = self.unfilledStarIcon

  def onHoverEvent(self, obj):
    ratingValue = 0
    for button in list(self.ratingButtonGroup.buttons()):
      button.icon = self.filledStarIcon
      ratingValue += 1
      if obj is button:
        break
    if self.showRatingValue:
      self.ratingLabel.setText(str(ratingValue))

  def onRatingButtonClicked(self, buttonId):
    self.ratingScore = buttonId
    if self.disabledWidget:
      self.disabledWidget.enabled = True
      self.disabledWidget = None
    if self.callback:
      self.callback(self.ratingScore)
    self.hide()


class WatchBoxAttribute(object):

  @property
  def title(self):
    return self.titleLabel.text

  @title.setter
  def title(self, value):
    self.titleLabel.text = value if value else ""

  @property
  def value(self):
    return self.valueLabel.text

  @value.setter
  def value(self, value):
    self.valueLabel.text = value if value else ""
    self.valueLabel.toolTip = value if value else ""

  def __init__(self, name, title, tags=None):
    self.name = name
    self.titleLabel = qt.QLabel()
    self.valueLabel = qt.QLabel()
    self.title = title
    self.tags = None if not tags else tags if type(tags) is list else [str(tags)]
    self.value = None


class BasicInformationWatchBox(qt.QGroupBox):

  DEFAULT_STYLE = 'background-color: rgb(230,230,230)'
  PREFERRED_DATE_FORMAT = "%Y-%b-%d"

  def __init__(self, attributes, title="", parent=None):
    super(BasicInformationWatchBox, self).__init__(title, parent)
    self.attributes = attributes
    if not self.checkAttributeUniqueness():
      raise ValueError("Attribute names are not unique.")
    self.setup()

  def checkAttributeUniqueness(self):
    onlyNames = [attribute.name for attribute in self.attributes]
    return len(self.attributes) == len(set(onlyNames))

  def reset(self):
    for attribute in self.attributes:
      attribute.value = ""

  def setup(self):
    self.setStyleSheet(self.DEFAULT_STYLE)
    layout = qt.QGridLayout()
    self.setLayout(layout)

    for index, attribute in enumerate(self.attributes):
      layout.addWidget(attribute.titleLabel, index, 0, 1, 1, qt.Qt.AlignLeft)
      layout.addWidget(attribute.valueLabel, index, 1, 1, 2)

  def getAttribute(self, name):
    for attribute in self.attributes:
      if attribute.name == name:
        return attribute
    return None

  def setInformation(self, attributeName, value, toolTip=None):
    attribute = self.getAttribute(attributeName)
    attribute.value = value
    attribute.valueLabel.toolTip = toolTip

  def getInformation(self, attributeName):
    attribute = self.getAttribute(attributeName)
    return attribute.value

  def formatDate(self, dateToFormat):
    if dateToFormat and dateToFormat != "":
      formatted = datetime.date(int(dateToFormat[0:4]), int(dateToFormat[4:6]), int(dateToFormat[6:8]))
      return formatted.strftime(self.PREFERRED_DATE_FORMAT)
    return "No Date found"

  def formatPatientName(self, name):
    if name != "":
      splitted = name.split('^')
      try:
        name = splitted[1] + ", " + splitted[0]
      except IndexError:
        name = splitted[0]
    return name


class FileBasedInformationWatchBox(BasicInformationWatchBox):

  DEFAULT_TAG_VALUE_SEPARATOR = ": "
  DEFAULT_TAG_NAME_SEPARATOR = "_"

  @property
  def sourceFile(self):
    return self._sourceFile

  @sourceFile.setter
  def sourceFile(self, filePath):
    self._sourceFile = filePath
    if filePath:
      self.updateInformation()
    else:
      self.reset()

  def __init__(self, attributes, title="", sourceFile=None, parent=None):
    super(FileBasedInformationWatchBox, self).__init__(attributes, title, parent)
    if sourceFile:
      self.sourceFile = sourceFile

  def _getTagNameFromTagNames(self, tagNames):
    return self.DEFAULT_TAG_NAME_SEPARATOR.join(tagNames)

  def _getTagValueFromTagValues(self, values):
    return self.DEFAULT_TAG_VALUE_SEPARATOR.join(values)

  def updateInformation(self):
    raise NotImplementedError


class XMLBasedInformationWatchBox(FileBasedInformationWatchBox):

  DATE_TAGS_TO_FORMAT = ["StudyDate", "PatientBirthDate", "SeriesDate", "ContentDate", "AcquisitionDate"]

  def __init__(self, attributes, title="", sourceFile=None, parent=None):
    super(XMLBasedInformationWatchBox, self).__init__(attributes, title, sourceFile, parent)

  def updateInformation(self):
    dom = xml.dom.minidom.parse(self._sourceFile)

    for attribute in self.attributes:
      values = []
      for tag in attribute.tags:
        currentValue = ModuleLogicMixin.findElement(dom, tag)
        if tag in self.DATE_TAGS_TO_FORMAT:
          currentValue = self.formatDate(currentValue)
        elif tag == "PatientName":
          currentValue = self.formatPatientName(currentValue)
        values.append(currentValue)
      value = self._getTagValueFromTagValues(values)
      self.setInformation(attribute.name, value, toolTip=value)


class DICOMBasedInformationWatchBox(FileBasedInformationWatchBox):

  DICOM_DATE_TAGS_TO_FORMAT = [DICOMTAGS.STUDY_DATE, DICOMTAGS.PATIENT_BIRTH_DATE]

  def __init__(self, attributes, title="", sourceFile=None, parent=None):
    super(DICOMBasedInformationWatchBox, self).__init__(attributes, title, sourceFile, parent)

  def updateInformation(self):
    for attribute in self.attributes:
      values = []
      for tag in attribute.tags:
        currentValue = ModuleLogicMixin.getDICOMValue(self.sourceFile, tag, "")
        if tag in self.DICOM_DATE_TAGS_TO_FORMAT:
          currentValue = self.formatDate(currentValue)
        elif tag == DICOMTAGS.PATIENT_NAME:
          currentValue = self.formatPatientName(currentValue)
        values.append(currentValue)
      value = self._getTagValueFromTagValues(values)
      self.setInformation(attribute.name, value, toolTip=value)


class CustomTargetTableModel(qt.QAbstractTableModel):

  COLUMN_NAME = 'Name'
  COLUMN_2D_DISTANCE = 'Distance 2D[mm]'
  COLUMN_3D_DISTANCE = 'Distance 3D[mm]'
  COLUMN_HOLE = 'Hole'
  COLUMN_DEPTH = 'Depth [mm]'

  headers = [COLUMN_NAME, COLUMN_2D_DISTANCE, COLUMN_3D_DISTANCE, COLUMN_HOLE, COLUMN_DEPTH]

  @property
  def targetList(self):
    return self._targetList

  @targetList.setter
  def targetList(self, targetList):
    self.needleStartEndPositions = {}
    if self._targetList and self.observer:
      self._targetList.RemoveObserver(self.observer)
    self._targetList = targetList
    if self._targetList:
      self.observer = self._targetList.AddObserver(self._targetList.PointModifiedEvent, self.computeNewDepthAndHole)
    self.computeNewDepthAndHole()
    self.reset()

  @property
  def cursorPosition(self):
    return self._cursorPosition

  @cursorPosition.setter
  def cursorPosition(self, cursorPosition):
    self._cursorPosition = cursorPosition
    self.dataChanged(self.index(0, 1), self.index(self.rowCount()-1, 2))

  def __init__(self, logic, targets=None, parent=None, *args):
    qt.QAbstractTableModel.__init__(self, parent, *args)
    self.logic = logic
    self._cursorPosition = None
    self._targetList = None
    self.needleStartEndPositions = {}
    self.targetList = targets
    self.computeCursorDistances = False
    self.zFrameDepths = {}
    self.zFrameHole = {}
    self.observer = None
    self._targetModifiedCallback = None

  def setTargetModifiedCallback(self, func):
    assert hasattr(func, '__call__')
    self._targetModifiedCallback = func

  def headerData(self, col, orientation, role):
    if orientation == qt.Qt.Horizontal and role in [qt.Qt.DisplayRole, qt.Qt.ToolTipRole]:
        return self.headers[col]
    return None

  def rowCount(self):
    try:
      number_of_targets = self.targetList.GetNumberOfFiducials()
      return number_of_targets
    except AttributeError:
      return 0

  def columnCount(self):
    return len(self.headers)

  def data(self, index, role):
    if not index.isValid() or role not in [qt.Qt.DisplayRole, qt.Qt.ToolTipRole]:
      return None

    row = index.row()
    col = index.column()

    targetPosition = [0.0, 0.0, 0.0]
    if col in [1,2,3,4]:
      self.targetList.GetNthFiducialPosition(row, targetPosition)

    if col == 0:
      return self.targetList.GetNthFiducialLabel(row)
    elif (col == 1 or col == 2) and self.cursorPosition and self.computeCursorDistances:
      if col == 1:
        distance2D = self.logic.get2DDistance(targetPosition, self.cursorPosition)
        return 'x = ' + str(round(distance2D[0], 2)) + ' y = ' + str(round(distance2D[1], 2))
      distance3D = self.logic.get3DDistance(targetPosition, self.cursorPosition)
      return str(round(distance3D, 2))

    elif (col == 3 or col == 4) and self.logic.zFrameRegistrationSuccessful:
      if col == 3:
        return self.computeZFrameHole(row, targetPosition)
      else:
        return self.computeZFrameDepth(row, targetPosition)
    return ""

  def computeZFrameHole(self, index, targetPosition):
    if index not in self.zFrameHole.keys():
      (start, end, indexX, indexY, depth, inRange) = self.logic.computeNearestPath(targetPosition)
      self.needleStartEndPositions[index] = (start, end)
      self.zFrameHole[index] = '(%s, %s)' % (indexX, indexY)
    return self.zFrameHole[index]

  def computeZFrameDepth(self, index, targetPosition):
    if index not in self.zFrameDepths.keys():
      (start, end, indexX, indexY, depth, inRange) = self.logic.computeNearestPath(targetPosition)
      self.zFrameDepths[index] = '%.3f' % depth if inRange else '(%.3f)' % depth
    return self.zFrameDepths[index]

  def computeNewDepthAndHole(self, observer=None, caller=None):
    self.zFrameDepths = {}
    self.zFrameHole = {}
    if not self.targetList or not self.logic.zFrameRegistrationSuccessful:
      return

    for index in range(self.targetList.GetNumberOfFiducials()):
      pos = [0.0, 0.0, 0.0]
      self.targetList.GetNthFiducialPosition(index, pos)
      self.computeZFrameHole(index, pos)

    self.dataChanged(self.index(0, 3), self.index(self.rowCount()-1, 4))
    if self._targetModifiedCallback:
      self._targetModifiedCallback()


class TargetCreationWidget(ModuleWidgetMixin):

  HEADERS = ["Name","Delete"]
  MODIFIED_EVENT = "ModifiedEvent"
  FIDUCIAL_LIST_OBSERVED_EVENTS = [MODIFIED_EVENT]

  @property
  def currentNode(self):
    return self._currentNode

  @currentNode.setter
  def currentNode(self, node):
    if self._currentNode:
      self.removeObservers()
    self._currentNode = node
    if node:
      self.placeWidget.setCurrentNode(node)
      self.addObservers()
    else:
      selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
      selectionNode.SetReferenceActivePlaceNodeID(None)
    self.updateTable()

  def __init__(self, parent, listModifiedCallback=None):
    self.parent = parent
    self.connectedButtons = []
    self.fiducialsNodeObservers = []
    self.setup()
    self._currentNode = None
    self.markupsLogic = slicer.modules.markups.logic()
    self.listModifiedCallback = listModifiedCallback

  def setup(self):
    self.placeWidget = slicer.qSlicerMarkupsPlaceWidget()
    self.placeWidget.setMRMLScene(slicer.mrmlScene)
    self.placeWidget.placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceMultipleMarkups

    self.table = qt.QTableWidget(0, 2)
    self.table.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
    self.table.setSelectionMode(qt.QAbstractItemView.SingleSelection)
    self.table.setMaximumHeight(200)
    self.table.horizontalHeader().setStretchLastSection(True)
    self.resetTable()
    self.parent.addRow(self.table)

    self.setupConnections()

  def setupConnections(self):
    self.table.connect("cellChanged (int,int)", self.onCellChanged)

  def reset(self):
    self.stopPlacing()
    self.currentNode = None

  def startPlacing(self):
    self.placeWidget.setPlaceModeEnabled(True)

  def stopPlacing(self):
    self.placeWidget.setPlaceModeEnabled(False)

  def createNewFiducialNode(self, name=None):
    self.currentNode = slicer.mrmlScene.GetNodeByID(self.markupsLogic.AddNewFiducialNode())
    self.currentNode.SetName(name if name else self.currentNode.GetName())

  def resetTable(self):
    self.cleanupButtons()
    self.table.clear()
    self.table.setHorizontalHeaderLabels(self.HEADERS)

  def cleanupButtons(self):
    for button in self.connectedButtons:
      button.clicked.disconnect(self.handleDeleteButtonClicked)
    self.connectedButtons = []

  def removeObservers(self):
    if self._currentNode and len(self.fiducialsNodeObservers) > 0:
      for observer in self.fiducialsNodeObservers:
        self._currentNode.RemoveObserver(observer)
    self.fiducialsNodeObservers = []

  def addObservers(self):
    if self.currentNode:
      for event in self.FIDUCIAL_LIST_OBSERVED_EVENTS:
        self.fiducialsNodeObservers.append(self.currentNode.AddObserver(event, self.onFiducialsUpdated))

  def updateTable(self):
    self.resetTable()
    if not self.currentNode:
      return
    nOfControlPoints = self.currentNode.GetNumberOfFiducials()
    if self.table.rowCount != nOfControlPoints:
      self.table.setRowCount(nOfControlPoints)
    for i in range(nOfControlPoints):
      label = self.currentNode.GetNthFiducialLabel(i)
      cellLabel = qt.QTableWidgetItem(label)
      self.table.setItem(i, 0, cellLabel)
      self.addDeleteButton(i, 1)
    self.table.show()

  def addDeleteButton(self, row, col):
    button = qt.QPushButton('X')
    self.table.setCellWidget(row, col, button)
    button.clicked.connect(lambda: self.handleDeleteButtonClicked(row))
    self.connectedButtons.append(button)

  def handleDeleteButtonClicked(self, idx):
    if slicer.util.confirmYesNoDisplay("Do you really want to delete fiducial %s?"
                                               % self.currentNode.GetNthFiducialLabel(idx), windowTitle="mpReview"):
      self.currentNode.RemoveMarkup(idx)

  def onFiducialsUpdated(self, caller, event):
    if caller.IsA("vtkMRMLMarkupsFiducialNode") and event == self.MODIFIED_EVENT:
      self.updateTable()
      if self.listModifiedCallback:
        self.listModifiedCallback()

  def onCellChanged(self, row, col):
    if col == 0:
      self.currentNode.SetNthFiducialLabel(row, self.table.item(row, col).text())