import qt, slicer
import vtk
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
      self.placeWidget.setCurrentNode(node)
      self.addTargetListObservers()
      self.markupsLogic.SetActiveListID(node)
    else:
      selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
      selectionNode.SetReferenceActivePlaceNodeID(None)
    self.updateTable()

  @property
  def targetListSelectorVisible(self):
    return self.targetListSelectorArea.visible

  @targetListSelectorVisible.setter
  def targetListSelectorVisible(self, visible):
    self.targetListSelectorArea.visible = visible

  def __init__(self, parent=None):
    qt.QWidget.__init__(self, parent)
    self.connectedButtons = []
    self.fiducialsNodeObservers = []
    self.setup()
    self._currentNode = None
    self.setupConnections()
    self.markupsLogic = slicer.modules.markups.logic()

  def setup(self):
    self.setLayout(qt.QGridLayout())
    self.placeWidget = slicer.qSlicerMarkupsPlaceWidget()
    self.placeWidget.setMRMLScene(slicer.mrmlScene)
    self.placeWidget.placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceMultipleMarkups
    self.setupTargetFiducialListSelector()
    self.setupTargetTable()

  def setupTargetFiducialListSelector(self):
    self.fiducialListSelector = self.createComboBox(nodeTypes=["vtkMRMLMarkupsFiducialNode", ""], addEnabled=True,
                                                    removeEnabled=True, noneEnabled=False, showChildNodeTypes=False,
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

  def setupConnections(self):
    self.fiducialListSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onFiducialListSelected)
    self.table.connect("cellChanged (int,int)", self.onCellChanged)

  def reset(self):
    self.stopPlacing()
    self.currentNode = None

  def onFiducialListSelected(self, node):
    self.currentNode = node

  def startPlacing(self):
    self.placeWidget.setPlaceModeEnabled(True)

  def stopPlacing(self):
    self.placeWidget.setPlaceModeEnabled(False)

  def createNewFiducialNode(self, name=None):
    self.currentNode = slicer.mrmlScene.GetNodeByID(self.markupsLogic.AddNewFiducialNode())
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
    if self.currentNode and len(self.fiducialsNodeObservers) > 0:
      for observer in self.fiducialsNodeObservers:
        self.currentNode.RemoveObserver(observer)
    self.fiducialsNodeObservers = []

  def addTargetListObservers(self):
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
      self.invokeEvent(vtk.vtkCommand.ModifiedEvent)

  def onCellChanged(self, row, col):
    if col == 0:
      self.currentNode.SetNthFiducialLabel(row, self.table.item(row, col).text())

  def getOrCreateFiducialNode(self):
    node = self.fiducialListSelector.currentNode()
    if not node:
      node = self.fiducialListSelector.addNode()
    return node