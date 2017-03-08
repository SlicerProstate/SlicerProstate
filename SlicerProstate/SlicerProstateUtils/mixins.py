import qt, vtk, ctk
import os, logging
import slicer
import SimpleITK as sitk
import sitkUtils
from SlicerProstateUtils.decorators import multimethod
from SlicerProstateUtils.widgets import CustomStatusProgressbar


class ParameterNodeObservationMixin(object):
  """
  This class can be used as a mixin for all classes that provide a method getParameterNode like
  ScriptedLoadableModuleLogic. ParameterNodeObservationMixin provides the possibility to simply
  observe the parameter node. Custom events can be observed and from your ScriptedLoadableModuleLogic
  invoked. Originated was this class from slicer.util.VTKObservationMixin
  """

  def __del__(self):
    self.removeEventObservers()

  @property
  def parameterNode(self):
    try:
      return self._parameterNode
    except AttributeError:
      self._parameterNode = self.getParameterNode() if hasattr(self, "getParameterNode") else self._createParameterNode()
    return self._parameterNode

  @property
  def parameterNodeObservers(self):
    try:
      return self._parameterNodeObservers
    except AttributeError:
      self._parameterNodeObservers = []
    return self._parameterNodeObservers

  def _createParameterNode(self):
    parameterNode = slicer.vtkMRMLScriptedModuleNode()
    slicer.mrmlScene.AddNode(parameterNode)
    return parameterNode

  def removeEventObservers(self, method=None):
    for e, m, g, t in list(self.parameterNodeObservers):
      if method == m or method is None:
        self.parameterNode.RemoveObserver(t)
        self.parameterNodeObservers.remove([e, m, g, t])

  def addEventObserver(self, event, method, group='none'):
    if self.hasEventObserver(event, method):
      self.removeEventObserver(event, method)
    tag = self.parameterNode.AddObserver(event, method)
    self.parameterNodeObservers.append([event, method, group, tag])

  def removeEventObserver(self, event, method):
    for e, m, g, t in self.parameterNodeObservers:
      if e == event and m == method:
        self.parameterNode.RemoveObserver(t)
        self.parameterNodeObservers.remove([e, m, g, t])

  def hasEventObserver(self, event, method):
    for e, m, g, t in self.parameterNodeObservers:
      if e == event and m == method:
        return True
    return False

  def invokeEvent(self, event, callData=None):
    if callData:
      self.parameterNode.InvokeEvent(event, callData)
    else:
      self.parameterNode.InvokeEvent(event)

  def getEventObservers(self):
    observerMethodDict = {}
    for e, m, g, t in self.parameterNodeObservers:
      observerMethodDict[e] = m
    return observerMethodDict


class GeneralModuleMixin(ParameterNodeObservationMixin):

  @staticmethod
  def getSlicerErrorLogPath():
    return slicer.app.errorLogModel().filePath

  @staticmethod
  def getTime():
    import datetime
    d = datetime.datetime.now()
    return d.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4] + "Z"

  def getSetting(self, setting, moduleName=None, default=None):
    moduleName = moduleName if moduleName else self.moduleName
    settings = qt.QSettings()
    setting = settings.value(moduleName + '/' + setting)
    return setting if setting else default

  def setSetting(self, setting, value, moduleName=None):
    moduleName = moduleName if moduleName else self.moduleName
    settings = qt.QSettings()
    settings.setValue(moduleName + '/' + setting, value)


class ModuleWidgetMixin(GeneralModuleMixin):

  @property
  def layoutManager(self):
    return slicer.app.layoutManager()

  @staticmethod
  def truncatePath(path):
    try:
      split = path.split('/')
      path = '.../' + split[-2] + '/' + split[-1]
    except (IndexError, AttributeError):
      pass
    return path

  def createSliceWidgetClassMembers(self, name):
    widget = self.layoutManager.sliceWidget(name)
    setattr(self, name.lower()+"Widget", widget)
    setattr(self, name.lower()+"CompositeNode", widget.mrmlSliceCompositeNode())
    setattr(self, name.lower()+"SliceView", widget.sliceView())
    setattr(self, name.lower()+"SliceViewInteractor", widget.sliceView().interactorStyle().GetInteractor())
    logic = widget.sliceLogic()
    setattr(self, name.lower()+"SliceLogic", logic)
    setattr(self, name.lower()+"SliceNode", logic.GetSliceNode())

  def getAllVisibleWidgets(self):
    visibleWidgets = []
    sliceLogics = self.layoutManager.mrmlSliceLogics()
    for n in range(sliceLogics.GetNumberOfItems()):
      sliceLogic = sliceLogics.GetItemAsObject(n)
      widget = self.layoutManager.sliceWidget(sliceLogic.GetName())
      if widget.sliceView().visible:
        visibleWidgets.append(widget)
    return visibleWidgets

  def getOrCreateCustomProgressBar(self):
    for child in slicer.util.mainWindow().statusBar().children():
      if isinstance(child, CustomStatusProgressbar):
        return child
    customStatusProgressBar = CustomStatusProgressbar()
    slicer.util.mainWindow().statusBar().addWidget(customStatusProgressBar, 1)
    return customStatusProgressBar

  @staticmethod
  def setFOV(sliceLogic, FOV):
    sliceNode = sliceLogic.GetSliceNode()
    sliceNode.SetFieldOfView(FOV[0], FOV[1], FOV[2])
    sliceNode.UpdateMatrices()

  @staticmethod
  def removeNodeFromMRMLScene(node):
    if node:
      slicer.mrmlScene.RemoveNode(node)
      node = None

  @staticmethod
  def refreshViewNodeIDs(node, sliceNodes):
    displayNode = node.GetDisplayNode()
    if displayNode:
      displayNode.RemoveAllViewNodeIDs()
      for sliceNode in sliceNodes:
        displayNode.AddViewNodeID(sliceNode.GetID())

  @staticmethod
  def removeViewNodeIDs(node, sliceNodes):
    displayNode = node.GetDisplayNode()
    if displayNode:
      displayNode.RemoveAllViewNodeIDs()
      for sliceNode in sliceNodes:
        displayNode.RemoveViewNodeID(sliceNode.GetID())

  @staticmethod
  def jumpSliceNodeToTarget(sliceNode, targetNode, index):
    point = [0,0,0,0]
    targetNode.GetMarkupPointWorld(index, 0, point)
    sliceNode.JumpSlice(point[0], point[1], point[2])

  @staticmethod
  def resetToRegularViewMode():
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SwitchToViewTransformMode()
    interactionNode.SetPlaceModePersistence(0)

  @staticmethod
  def confirmOrSaveDialog(message, title='mpReview'):
    box = qt.QMessageBox(qt.QMessageBox.Question, title, message)
    box.addButton("Exit, discard changes", qt.QMessageBox.AcceptRole)
    box.addButton("Save changes", qt.QMessageBox.ActionRole)
    box.addButton("Cancel", qt.QMessageBox.RejectRole)
    return box.exec_()

  def updateProgressBar(self, **kwargs):
    progress = kwargs.pop('progress', None)
    assert progress, "Keyword argument progress (instance of QProgressDialog) is missing"
    for key, value in kwargs.iteritems():
      if hasattr(progress, key):
        setattr(progress, key, value)
      else:
        print "key %s not found" % key
    slicer.app.processEvents()

  def createHLayout(self, elements, **kwargs):
    return self._createLayout(qt.QHBoxLayout, elements, **kwargs)

  def createVLayout(self, elements, **kwargs):
    return self._createLayout(qt.QVBoxLayout, elements, **kwargs)

  def _createLayout(self, layoutClass, elements, **kwargs):
    widget = qt.QWidget()
    rowLayout = layoutClass()
    widget.setLayout(rowLayout)
    for element in elements:
      rowLayout.addWidget(element)
    for key, value in kwargs.iteritems():
      if hasattr(rowLayout, key):
        setattr(rowLayout, key, value)
    return widget

  def _createListView(self, name, headerLabels):
    view = qt.QListView()
    view.setObjectName(name)
    view.setSpacing(3)
    model = qt.QStandardItemModel()
    model.setHorizontalHeaderLabels(headerLabels)
    view.setModel(model)
    view.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
    return view, model

  def createIcon(self, filename, iconPath=None):
    if not iconPath:
      iconPath = os.path.join(self.modulePath, 'Resources/Icons')
    path = os.path.join(iconPath, filename)
    pixmap = qt.QPixmap(path)
    return qt.QIcon(pixmap)

  def createSliderWidget(self, minimum, maximum):
    slider = slicer.qMRMLSliderWidget()
    slider.minimum = minimum
    slider.maximum = maximum
    return slider

  def createLabel(self, title, **kwargs):
    label = qt.QLabel(title)
    return self.extendQtGuiElementProperties(label, **kwargs)

  def createLineEdit(self, title, **kwargs):
    lineEdit = qt.QLineEdit(title)
    return self.extendQtGuiElementProperties(lineEdit, **kwargs)

  def createButton(self, title, buttonClass=qt.QPushButton, **kwargs):
    button = buttonClass(title)
    button.setCursor(qt.Qt.PointingHandCursor)
    return self.extendQtGuiElementProperties(button, **kwargs)

  def createRadioButton(self, text, **kwargs):
    button = qt.QRadioButton(text)
    button.setCursor(qt.Qt.PointingHandCursor)
    return self.extendQtGuiElementProperties(button, **kwargs)

  def createDirectoryButton(self, **kwargs):
    button = ctk.ctkDirectoryButton()
    for key, value in kwargs.iteritems():
      if hasattr(button, key):
        setattr(button, key, value)
    return button

  def extendQtGuiElementProperties(self, element, **kwargs):
    for key, value in kwargs.iteritems():
      if hasattr(element, key):
        setattr(element, key, value)
      else:
        if key == "fixedHeight":
          element.minimumHeight = value
          element.maximumHeight = value
        elif key == 'hidden':
          if value:
            element.hide()
          else:
            element.show()
        else:
          logging.error("%s does not have attribute %s" % (element.className(), key))
    return element

  def createComboBox(self, **kwargs):
    combobox = slicer.qMRMLNodeComboBox()
    combobox.addEnabled = False
    combobox.removeEnabled = False
    combobox.noneEnabled = True
    combobox.showHidden = False
    for key, value in kwargs.iteritems():
      if hasattr(combobox, key):
        setattr(combobox, key, value)
      else:
        logging.error("qMRMLNodeComboBox does not have attribute %s" % key)
    combobox.setMRMLScene(slicer.mrmlScene)
    return combobox

  def showMainAppToolbars(show=True):
    w = slicer.util.mainWindow()
    for c in w.children():
      if str(type(c)).find('ToolBar')>0:
        if show:
          c.show()
        else:
          c.hide()

  def createProgressDialog(self, parent=None, value=0, maximum=100, labelText="", windowTitle="Processing...",
                           windowFlags=None, **kwargs):
    """Display a modal QProgressDialog. Go to QProgressDialog documentation
    http://pyqt.sourceforge.net/Docs/PyQt4/qprogressdialog.html for more keyword arguments, that could be used.
    E.g. progressbar = createProgressIndicator(autoClose=False) if you don't want the progress dialog to automatically
    close.
    Updating progress value with progressbar.value = 50
    Updating label text with progressbar.labelText = "processing XYZ"
    """
    progressIndicator = qt.QProgressDialog(parent if parent else slicer.util.mainWindow(),
                                           windowFlags if windowFlags else qt.Qt.WindowStaysOnTopHint)
    progressIndicator.minimumDuration = 0
    progressIndicator.maximum = maximum
    progressIndicator.value = value
    progressIndicator.windowTitle = windowTitle
    progressIndicator.labelText = labelText
    for key, value in kwargs.iteritems():
      if hasattr(progressIndicator, key):
        setattr(progressIndicator, key, value)
    return progressIndicator


class ModuleLogicMixin(GeneralModuleMixin):

  @staticmethod
  def cloneFiducials(original, cloneName, keepDisplayNode=False):
    clone = slicer.vtkMRMLMarkupsFiducialNode()
    clone.Copy(original)
    clone.SetName(cloneName)
    slicer.mrmlScene.AddNode(clone)
    if not keepDisplayNode:
      displayNode = slicer.vtkMRMLMarkupsDisplayNode()
      slicer.mrmlScene.AddNode(displayNode)
      clone.SetAndObserveDisplayNodeID(displayNode.GetID())
    return clone

  @staticmethod
  def getMostRecentFile(path, fileType, filter=None):
    assert type(fileType) is str
    files = [f for f in os.listdir(path) if f.endswith(fileType)]
    if len(files) == 0:
      return None
    mostRecent = None
    storedTimeStamp = 0
    for filename in files:
      if filter and not filter in filename:
        continue
      actualFileName = filename.split(".")[0]
      timeStamp = int(actualFileName.split("-")[-1])
      if timeStamp > storedTimeStamp:
        mostRecent = filename
        storedTimeStamp = timeStamp
    return mostRecent

  @staticmethod
  def createTimer(interval, slot, singleShot=False):
    timer = qt.QTimer()
    timer.setInterval(interval)
    timer.timeout.connect(slot)
    timer.setSingleShot(singleShot)
    return timer

  @staticmethod
  def getTargetPosition(targetNode, index):
    position = [0.0, 0.0, 0.0]
    targetNode.GetNthFiducialPosition(index, position)
    return position

  @staticmethod
  def get3DDistance(p1, p2):
    return [abs(p1[0]-p2[0]), abs(p1[1]-p2[1]), abs(p1[2]-p2[2])]

  @staticmethod
  def get3DEuclideanDistance(pos1, pos2):
    rulerNode = slicer.vtkMRMLAnnotationRulerNode()
    rulerNode.SetPosition1(pos1)
    rulerNode.SetPosition2(pos2)
    distance3D = rulerNode.GetDistanceMeasurement()
    return distance3D

  @staticmethod
  def dilateMask(label, dilateValue=1.0, erodeValue=0.0, marginSize=5.0):
    imagedata = label.GetImageData()
    dilateErode = vtk.vtkImageDilateErode3D()
    dilateErode.SetInputData(imagedata)
    dilateErode.SetDilateValue(dilateValue)
    dilateErode.SetErodeValue(erodeValue)
    spacing = label.GetSpacing()
    kernelSizePixel = [int(round((abs(marginSize) / spacing[componentIndex]+1)/2)*2-1) for componentIndex in range(3)]
    dilateErode.SetKernelSize(kernelSizePixel[0], kernelSizePixel[1], kernelSizePixel[2])
    dilateErode.Update()
    label.SetAndObserveImageData(dilateErode.GetOutput())

  @staticmethod
  def getCentroidForLabel(labelNode, value):
    if not labelNode:
      return None
    labelAddress = sitkUtils.GetSlicerITKReadWriteAddress(labelNode.GetName())
    labelImage = sitk.ReadImage(labelAddress)

    ls = sitk.LabelStatisticsImageFilter()
    ls.Execute(labelImage, labelImage)
    bb = ls.GetBoundingBox(value)

    centroid = None # sagittal, coronal, axial
    if len(bb) > 0:
      centerIJK = [((bb[0] + bb[1]) / 2), ((bb[2] + bb[3]) / 2), ((bb[4] + bb[5]) / 2)]
      logging.debug('BB is: ' + str(bb))
      logging.debug('i_center = '+str(centerIJK[0]))
      logging.debug('j_center = '+str(centerIJK[1]))
      logging.debug('k_center = '+str(centerIJK[2]))

      IJKtoRAS = vtk.vtkMatrix4x4()
      labelNode.GetIJKToRASMatrix(IJKtoRAS)
      IJKtoRASDir = vtk.vtkMatrix4x4()
      labelNode.GetIJKToRASDirectionMatrix(IJKtoRASDir)
      RAScoord = IJKtoRAS.MultiplyPoint((centerIJK[0], centerIJK[1], centerIJK[2], 1))

      order = labelNode.ComputeScanOrderFromIJKToRAS(IJKtoRAS)
      if order == 'IS':
        RASDir = IJKtoRASDir.MultiplyPoint((RAScoord[0], RAScoord[1], RAScoord[2], 1))
        centroid = [-RASDir[0], -RASDir[1], RASDir[2]]
      elif order == 'AP':
        RASDir = IJKtoRASDir.MultiplyPoint((RAScoord[0], RAScoord[1], RAScoord[2], 1))
        centroid = [-RASDir[0], -RASDir[2], -RASDir[1]]
      elif order == 'LR':
        RASDir = IJKtoRASDir.MultiplyPoint((RAScoord[2], RAScoord[1], RAScoord[0], 1))
        centroid = [RASDir[0], -RASDir[2], -RASDir[1]]
    return centroid

  @staticmethod
  def applyOtsuFilter(volume):
    outputVolume = slicer.vtkMRMLScalarVolumeNode()
    outputVolume.SetName('ZFrame_Otsu_Output')
    slicer.mrmlScene.AddNode(outputVolume)
    params = {'inputVolume': volume.GetID(),
              'outputVolume': outputVolume.GetID(),
              'insideValue': 0, 'outsideValue': 1}

    slicer.cli.run(slicer.modules.otsuthresholdimagefilter, None, params, wait_for_completion=True)
    return outputVolume

  @staticmethod
  def getDirectorySize(directory):
    size = 0
    for path, dirs, files in os.walk(directory):
      for currentFile in files:
        if not ".DS_Store" in currentFile:
          size += os.path.getsize(os.path.join(path, currentFile))
    return size

  @staticmethod
  def createDirectory(directory, message=None):
    if message:
      logging.debug(message)
    try:
      os.makedirs(directory)
    except OSError:
      logging.debug('Failed to create the following directory: ' + directory)

  @staticmethod
  def findElement(dom, name):
    for e in [e for e in dom.getElementsByTagName('element') if e.getAttribute('name') == name]:
      try:
        return e.childNodes[0].nodeValue
      except IndexError:
        return ""

  @staticmethod
  @multimethod([str, unicode], [str, unicode])
  def getDICOMValue(currentFile, tag):
    return ModuleLogicMixin.getDICOMValue(currentFile, tag, "")

  @staticmethod
  @multimethod([str, unicode], [str, unicode], [str, unicode])
  def getDICOMValue(currentFile, tag, default):
    try:
      return slicer.dicomDatabase.fileValue(currentFile, tag)
    except RuntimeError:
      logging.info("There are problems with accessing DICOM value %s from file %s" % (tag, currentFile))
    return default

  @staticmethod
  @multimethod(slicer.vtkMRMLScalarVolumeNode, [str, unicode])
  def getDICOMValue(volumeNode, tag):
    return ModuleLogicMixin.getDICOMValue(volumeNode, tag, "")

  @staticmethod
  @multimethod(slicer.vtkMRMLScalarVolumeNode, [str, unicode], [str, unicode])
  def getDICOMValue(volumeNode, tag, default):
    try:
      currentFile = volumeNode.GetStorageNode().GetFileName()
      return ModuleLogicMixin.getDICOMValue(currentFile, tag, default)
    except (RuntimeError, AttributeError):
      logging.info("There are problems with accessing DICOM value %s from volume node %s" % (tag, volumeNode.GetID()))
    return default

  @staticmethod
  def getFileList(directory):
    return [f for f in os.listdir(directory) if ".DS_Store" not in f]

  @staticmethod
  def importStudy(dicomDataDir):
    indexer = ctk.ctkDICOMIndexer()
    indexer.addDirectory(slicer.dicomDatabase, dicomDataDir)
    indexer.waitForImportFinished()

  @staticmethod
  def createScalarVolumeNode(name=None):
    return ModuleLogicMixin.createNode(slicer.vtkMRMLScalarVolumeNode, name=name)

  @staticmethod
  def createBSplineTransformNode(name=None):
    return ModuleLogicMixin.createNode(slicer.vtkMRMLBSplineTransformNode, name=name)

  @staticmethod
  def createLinearTransformNode(name=None):
    return ModuleLogicMixin.createNode(slicer.vtkMRMLLinearTransformNode, name=name)

  @staticmethod
  def createModelNode(name=None):
    return ModuleLogicMixin.createNode(slicer.vtkMRMLModelNode, name=name)

  @staticmethod
  def createNode(nodeType, name=None):
    node = nodeType()
    if name:
      node.SetName(name)
    slicer.mrmlScene.AddNode(node)
    return node

  @staticmethod
  def saveNodeData(node, outputDir, extension, replaceUnwantedCharacters=True, name=None, overwrite=False):
    name = name if name else node.GetName()
    if replaceUnwantedCharacters:
      name = ModuleLogicMixin.replaceUnwantedCharacters(name)
    filename = os.path.join(outputDir, name + extension)
    if os.path.exists(filename) and not overwrite:
      return True, name
    return slicer.util.saveNode(node, filename), name

  @staticmethod
  def replaceUnwantedCharacters(string, characters=None, replaceWith="-"):
    if not characters:
      characters = [": ", " ", ":", "/"]
    for character in characters:
      string = string.replace(character, replaceWith)
    return string

  @staticmethod
  def handleSaveNodeDataReturn(success, name, successfulList, failedList):
    listToAdd = successfulList if success else failedList
    listToAdd.append(name)

  @staticmethod
  def applyTransform(transform, node):
    tfmLogic = slicer.modules.transforms.logic()
    node.SetAndObserveTransformNodeID(transform.GetID())
    tfmLogic.hardenTransform(node)

  @staticmethod
  def setAndObserveDisplayNode(node):
    displayNode = slicer.vtkMRMLModelDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)
    node.SetAndObserveDisplayNodeID(displayNode.GetID())
    return displayNode

  @staticmethod
  def isVolumeExtentValid(volume):
    imageData = volume.GetImageData()
    try:
      extent = imageData.GetExtent()
      return extent[1] > 0 and extent[3] > 0 and extent[5] > 0
    except AttributeError:
      return False