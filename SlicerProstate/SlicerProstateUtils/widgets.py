import qt
import slicer
import vtk
import os
import sys
from mixins import ModuleWidgetMixin
from decorators import singleton


@singleton
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
    slicer.util.mainWindow().statusBar().addWidget(self, 1)

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


class TargetCreationWidget(qt.QWidget, ModuleWidgetMixin):

  HEADERS = ["Name","Delete"]
  MODIFIED_EVENT = "ModifiedEvent"
  FIDUCIAL_LIST_OBSERVED_EVENTS = [MODIFIED_EVENT]

  DEFAULT_FIDUCIAL_LIST_NAME = None
  DEFAULT_CREATE_FIDUCIALS_TEXT = "Place Target(s)"
  DEFAULT_MODIFY_FIDUCIALS_TEXT = "Modify Target(s)"

  TargetingStartedEvent = vtk.vtkCommand.UserEvent + 335
  TargetingFinishedEvent = vtk.vtkCommand.UserEvent + 336

  ICON_SIZE = qt.QSize(24, 24)

  @property
  def currentNode(self):
    return self.fiducialListSelector.currentNode()

  @currentNode.setter
  def currentNode(self, node):
    if self._currentNode:
      self.removeTargetListObservers()
    self.fiducialListSelector.setCurrentNode(node)
    self._currentNode = node
    if node:
      self.addTargetListObservers()
      self.selectionNode.SetReferenceActivePlaceNodeID(node.GetID())
    else:
      self.selectionNode.SetReferenceActivePlaceNodeID(None)

    self.updateButtons()
    self.updateTable()

  @property
  def targetListSelectorVisible(self):
    return self.targetListSelectorArea.visible

  @targetListSelectorVisible.setter
  def targetListSelectorVisible(self, visible):
    self.targetListSelectorArea.visible = visible

  def __init__(self, parent=None, **kwargs):
    qt.QWidget.__init__(self, parent)
    self.iconPath = os.path.join(os.path.dirname(sys.modules[self.__module__].__file__), '../Resources/Icons')
    self.processKwargs(**kwargs)
    self.connectedButtons = []
    self.fiducialNodeObservers = []
    self.selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
    self.interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    self.setupIcons()
    self.setup()
    self._currentNode = None
    self.setupConnections()

  def processKwargs(self, **kwargs):
    for key, value in kwargs.iteritems():
      if hasattr(self, key):
        setattr(self, key, value)

  def reset(self):
    self.stopPlacing()
    self.currentNode = None

  def setupIcons(self):
    self.setTargetsIcon = self.createIcon("icon-addFiducial.png", self.iconPath)
    self.modifyTargetsIcon = self.createIcon("icon-modifyFiducial.png", self.iconPath)
    self.finishIcon = self.createIcon("icon-apply.png", self.iconPath)

  def setup(self):
    self.setLayout(qt.QGridLayout())
    self.setupTargetFiducialListSelector()
    self.setupTargetTable()
    self.setupButtons()

  def setupTargetFiducialListSelector(self):
    self.fiducialListSelector = self.createComboBox(nodeTypes=["vtkMRMLMarkupsFiducialNode", ""], addEnabled=True,
                                                    removeEnabled=True, noneEnabled=True, showChildNodeTypes=False,
                                                    selectNodeUponCreation=True, toolTip="Select target list")
    self.targetListSelectorArea = self.createHLayout([qt.QLabel("Target List: "), self.fiducialListSelector])
    self.targetListSelectorArea.hide()
    self.layout().addWidget(self.targetListSelectorArea)

  def setupTargetTable(self):
    self.table = qt.QTableWidget(0, 2)
    self.table.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
    self.table.setSelectionMode(qt.QAbstractItemView.SingleSelection)
    self.table.setMaximumHeight(200)
    self.table.horizontalHeader().setStretchLastSection(True)
    self.resetTable()
    self.layout().addWidget(self.table)

  def setupButtons(self):
    self.startTargetingButton = self.createButton("", enabled=True, icon=self.setTargetsIcon, iconSize=self.ICON_SIZE,
                                                  toolTip="Start placing targets")
    self.stopTargetingButton = self.createButton("", enabled=False, icon=self.finishIcon, iconSize=self.ICON_SIZE,
                                                 toolTip="Finish placing targets")
    self.buttons = self.createHLayout([self.startTargetingButton, self.stopTargetingButton])
    self.layout().addWidget(self.buttons)

  def setupConnections(self):
    self.startTargetingButton.clicked.connect(self.startPlacing)
    self.stopTargetingButton.clicked.connect(self.stopPlacing)
    # TODO: think about the following since it will always listen!
    self.interactionNodeObserver = self.interactionNode.AddObserver(self.interactionNode.InteractionModeChangedEvent,
                                                                    self.onInteractionModeChanged)
    self.fiducialListSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onFiducialListSelected)
    self.table.connect("cellChanged (int,int)", self.onCellChanged)

  def onInteractionModeChanged(self, caller, event):
    if not self.currentNode:
      return
    if self.selectionNode.GetActivePlaceNodeID() == self.currentNode.GetID():
      interactionMode = self.interactionNode.GetCurrentInteractionMode()
      self.invokeEvent(self.TargetingStartedEvent if interactionMode == self.interactionNode.Place else
                       self.TargetingFinishedEvent)
      self.updateButtons()

  def onFiducialListSelected(self, node):
    self.currentNode = node

  def startPlacing(self):
    if not self.currentNode:
      self.createNewFiducialNode(name=self.DEFAULT_FIDUCIAL_LIST_NAME)
    self.selectionNode.SetReferenceActivePlaceNodeID(self.currentNode.GetID())
    self.interactionNode.SetPlaceModePersistence(1)
    self.interactionNode.SetCurrentInteractionMode(self.interactionNode.Place)

  def stopPlacing(self):
    self.interactionNode.SetCurrentInteractionMode(self.interactionNode.ViewTransform)

  def createNewFiducialNode(self, name=None):
    markupsLogic = slicer.modules.markups.logic()
    self.currentNode = slicer.mrmlScene.GetNodeByID(markupsLogic.AddNewFiducialNode())
    self.currentNode.SetName(name if name else self.currentNode.GetName())

  def resetTable(self):
    self.cleanupButtons()
    self.table.setRowCount(0)
    self.table.clear()
    self.table.setHorizontalHeaderLabels(self.HEADERS)

  def cleanupButtons(self):
    for button in self.connectedButtons:
      button.clicked.disconnect(self.handleDeleteButtonClicked)
    self.connectedButtons = []

  def removeTargetListObservers(self):
    if self.currentNode and len(self.fiducialNodeObservers) > 0:
      for observer in self.fiducialNodeObservers:
        self.currentNode.RemoveObserver(observer)
    self.fiducialNodeObservers = []

  def addTargetListObservers(self):
    if self.currentNode:
      for event in self.FIDUCIAL_LIST_OBSERVED_EVENTS:
        self.fiducialNodeObservers.append(self.currentNode.AddObserver(event, self.onFiducialsUpdated))

  def updateButtons(self):
    if not self.currentNode or self.currentNode.GetNumberOfFiducials() == 0:
      self.startTargetingButton.icon = self.setTargetsIcon
      self.startTargetingButton.toolTip = "Place Target(s)"
    else:
      self.startTargetingButton.icon = self.modifyTargetsIcon
      self.startTargetingButton.toolTip = "Modify Target(s)"
    interactionMode = self.interactionNode.GetCurrentInteractionMode()
    self.startTargetingButton.enabled = not interactionMode == self.interactionNode.Place
    self.stopTargetingButton.enabled = interactionMode == self.interactionNode.Place

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
      self.updateButtons()
      self.invokeEvent(vtk.vtkCommand.ModifiedEvent)

  def onCellChanged(self, row, col):
    if col == 0:
      self.currentNode.SetNthFiducialLabel(row, self.table.item(row, col).text())

  def getOrCreateFiducialNode(self):
    node = self.fiducialListSelector.currentNode()
    if not node:
      node = self.fiducialListSelector.addNode()
    return node

  def hasTargetListAtLeastOneTarget(self):
    return self.currentNode is not None and self.currentNode.GetNumberOfFiducials() > 0
