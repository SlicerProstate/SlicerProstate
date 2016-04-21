import qt, vtk, ctk
import os, logging
import slicer


class ModuleWidgetMixin(object):

  @property
  def layoutManager(self):
    return slicer.app.layoutManager()

  @property
  def dicomDatabase(self):
    return slicer.dicomDatabase

  @staticmethod
  def truncatePath(path):
    try:
      split = path.split('/')
      path = '.../' + split[-2] + '/' + split[-1]
    except (IndexError, AttributeError):
      pass
    return path

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
  def jumpSliceNodeToTarget(sliceNode, targetNode, index):
    point = [0,0,0,0]
    targetNode.GetMarkupPointWorld(index, 0, point)
    sliceNode.JumpSlice(point[0], point[1], point[2])

  @staticmethod
  def resetToRegularViewMode():
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SwitchToViewTransformMode()
    interactionNode.SetPlaceModePersistence(0)

  def getSetting(self, setting, moduleName=None):
    moduleName = moduleName if moduleName else self.moduleName
    settings = qt.QSettings()
    setting = settings.value(self.moduleName + '/' + setting)
    return setting

  def setSetting(self, setting, value, moduleName=None):
    moduleName = moduleName if moduleName else self.moduleName
    settings = qt.QSettings()
    settings.setValue(moduleName + '/' + setting, value)

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

  def createButton(self, title, **kwargs):
    button = qt.QPushButton(title)
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



class ModuleLogicMixin(object):

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
  def get2DDistance(pos1, pos2):
    x = abs(pos1[0] - pos2[0])
    y = abs(pos1[1] - pos2[1])
    return [x, y]

  @staticmethod
  def get3DDistance(pos1, pos2):
    rulerNode = slicer.vtkMRMLAnnotationRulerNode()
    rulerNode.SetPosition1(pos1)
    rulerNode.SetPosition2(pos2)
    distance_3D = rulerNode.GetDistanceMeasurement()
    return distance_3D

  @staticmethod
  def dilateMask(label):
    imagedata = label.GetImageData()
    dilateErode = vtk.vtkImageDilateErode3D()
    dilateErode.SetInputData(imagedata)
    dilateErode.SetDilateValue(1.0)
    dilateErode.SetErodeValue(0.0)
    dilateErode.SetKernelSize(12, 12, 1)
    dilateErode.Update()
    label.SetAndObserveImageData(dilateErode.GetOutput())

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
  def getDICOMValue(currentFile, tag, fallback=None):
    db = slicer.dicomDatabase
    try:
      value = db.fileValue(currentFile, tag)
    except RuntimeError:
      logging.info("There are problems with accessing DICOM value %s from file %s" % (tag, currentFile))
      value = fallback
    return value

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


class ParameterNodeObservationMixin(object):
  """
  This class can be used as a mixin for all classes that provide a method getParameterNode like
  ScriptedLoadableModuleLogic. ParameterNodeObservationMixin provides the possibility to simply
  observe the parameter node. Custom events can be observed and from your ScriptedLoadableModuleLogic
  invoked. Originated was this class from slicer.util.VTKObservationMixin
  """

  @property
  def parameterNode(self):
    try:
      return self._parameterNode
    except AttributeError:
      self._parameterNode = self.getParameterNode()
    return self._parameterNode

  @property
  def parameterNodeObservations(self):
    try:
      return self._parameterNodeObservations
    except AttributeError:
      self._parameterNodeObservations = []
    return self._parameterNodeObservations

  def getParameterNode(self):
    """If this mixin is used in a ScriptedLoadableModuleLogic
    inherited class, it should be overwritten with:
    return ScriptedLoadableModuleLogic.getParameterNode(self)
    """
    return NotImplementedError

  def removeObservers(self, method=None):
    for e, m, g, t in list(self.parameterNodeObservations):
      if method == m or method is None:
        self.parameterNode.RemoveObserver(t)
        self.parameterNodeObservations.remove([e, m, g, t])

  def addObserver(self, event, method, group='none'):
    if self.hasObserver(event, method):
      self.removeObserver(event, method)
    tag = self.parameterNode.AddObserver(event, method)
    self.parameterNodeObservations.append([event, method, group, tag])

  def removeObserver(self, event, method):
    for e, m, g, t in self.parameterNodeObservations:
      if e == event and m == method:
        self.parameterNode.RemoveObserver(t)
        self.parameterNodeObservations.remove([e, m, g, t])

  def hasObserver(self, event, method):
    for e, m, g, t in self.parameterNodeObservations:
      if e == event and m == method:
        return True
    return False

  def invokeEvent(self, event):
    self.parameterNode.InvokeEvent(event)