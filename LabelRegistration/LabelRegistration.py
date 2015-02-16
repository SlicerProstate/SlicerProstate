import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

import SimpleITK as sitk
import sitkUtils

#
# LabelRegistration
#

class LabelRegistration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py

  This module is scripted and not CLI because we would like to use BRAINSFit, and that is easier to do from a scripted module.
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LabelRegistration" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Registration"]
    self.parent.dependencies = ['SegmentationSmoothing','QuadEdgeSurfaceMesher']
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# LabelRegistrationWidget
#

class LabelRegistrationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # fixed image selector
    #
    self.fixedImageSelector = slicer.qMRMLNodeComboBox()
    self.fixedImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.fixedImageSelector.selectNodeUponCreation = True
    self.fixedImageSelector.addEnabled = False
    self.fixedImageSelector.removeEnabled = False
    self.fixedImageSelector.noneEnabled = False
    self.fixedImageSelector.showHidden = False
    self.fixedImageSelector.showChildNodeTypes = False
    self.fixedImageSelector.setMRMLScene( slicer.mrmlScene )
    self.fixedImageSelector.setToolTip( "Fixed image" )
    parametersFormLayout.addRow("Fixed Image: ", self.fixedImageSelector)

    #
    # fixed image label selector
    #
    self.fixedImageLabelSelector = slicer.qMRMLNodeComboBox()
    self.fixedImageLabelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.fixedImageLabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.fixedImageLabelSelector.selectNodeUponCreation = True
    self.fixedImageLabelSelector.addEnabled = False
    self.fixedImageLabelSelector.removeEnabled = False
    self.fixedImageLabelSelector.noneEnabled = False
    self.fixedImageLabelSelector.showHidden = False
    self.fixedImageLabelSelector.showChildNodeTypes = False
    self.fixedImageLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.fixedImageLabelSelector.setToolTip( "Segmentation of the fixed image" )
    parametersFormLayout.addRow("Segmentation of the fixed Image: ", self.fixedImageLabelSelector)

    #
    # moving image selector
    #
    self.movingImageSelector = slicer.qMRMLNodeComboBox()
    self.movingImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.movingImageSelector.selectNodeUponCreation = True
    self.movingImageSelector.addEnabled = False
    self.movingImageSelector.removeEnabled = False
    self.movingImageSelector.noneEnabled = False
    self.movingImageSelector.showHidden = False
    self.movingImageSelector.showChildNodeTypes = False
    self.movingImageSelector.setMRMLScene( slicer.mrmlScene )
    self.movingImageSelector.setToolTip( "Moving image" )
    parametersFormLayout.addRow("Moving Image: ", self.movingImageSelector)

    #
    # moving image label selector
    #
    self.movingImageLabelSelector = slicer.qMRMLNodeComboBox()
    self.movingImageLabelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.movingImageLabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.movingImageLabelSelector.selectNodeUponCreation = True
    self.movingImageLabelSelector.addEnabled = False
    self.movingImageLabelSelector.removeEnabled = False
    self.movingImageLabelSelector.noneEnabled = False
    self.movingImageLabelSelector.showHidden = False
    self.movingImageLabelSelector.showChildNodeTypes = False
    self.movingImageLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.movingImageLabelSelector.setToolTip( "Segmentation of the moving image" )
    parametersFormLayout.addRow("Segmentation of the moving Image: ", self.movingImageLabelSelector)

    #
    # Affine output transform selector
    #
    self.affineTransformSelector = slicer.qMRMLNodeComboBox()
    self.affineTransformSelector.nodeTypes = ( ("vtkMRMLTransformNode"), "" )
    self.affineTransformSelector.selectNodeUponCreation = True
    self.affineTransformSelector.addEnabled = True
    self.affineTransformSelector.removeEnabled = False
    self.affineTransformSelector.noneEnabled = False
    self.affineTransformSelector.showHidden = False
    self.affineTransformSelector.showChildNodeTypes = False # ?
    self.affineTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.affineTransformSelector.setToolTip( "Registration affine transform" )
    parametersFormLayout.addRow("Registration affine transform: ", self.affineTransformSelector)

    #
    # B-spline output transform selector
    #
    self.bsplineTransformSelector = slicer.qMRMLNodeComboBox()
    self.bsplineTransformSelector.nodeTypes = ( ("vtkMRMLTransformNode"), "" )
    self.bsplineTransformSelector.selectNodeUponCreation = True
    self.bsplineTransformSelector.addEnabled = True
    self.bsplineTransformSelector.removeEnabled = False
    self.bsplineTransformSelector.noneEnabled = False
    self.bsplineTransformSelector.showHidden = False
    self.bsplineTransformSelector.showChildNodeTypes = False # ?
    self.bsplineTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.bsplineTransformSelector.setToolTip( "Registration b-spline transform" )
    parametersFormLayout.addRow("Registration B-spline Transform: ", self.bsplineTransformSelector)

    #
    # registered volume selector
    #
    self.outputImageSelector = slicer.qMRMLNodeComboBox()
    self.outputImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    # self.outputImageSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
    self.outputImageSelector.selectNodeUponCreation = True
    self.outputImageSelector.addEnabled = True
    self.outputImageSelector.removeEnabled = True
    self.outputImageSelector.noneEnabled = True
    self.outputImageSelector.showHidden = False
    self.outputImageSelector.showChildNodeTypes = False
    self.outputImageSelector.setMRMLScene( slicer.mrmlScene )
    self.outputImageSelector.setToolTip( "Registered volume" )
    parametersFormLayout.addRow("Registered Volume: ", self.outputImageSelector)

    #
    # To be added later: advanced parameters
    #  registration modes (rigid/affine/bspline), save rigid/affine transforms,
    #  crop box margin, number of samples, ...
    #
    # Add parameter node to facilitate registration from other modules and
    # command line
    #

    self.visualizationCheckbox = qt.QCheckBox()
    parametersFormLayout.addRow("Visualize results:",self.visualizationCheckbox)

    groupLabel = qt.QLabel('Visualization mode:')
    self.registrationModeGroup = qt.QButtonGroup()
    self.noRegistrationRadio = qt.QRadioButton('No registration')
    self.linearRegistrationRadio = qt.QRadioButton('Linear registration')
    self.deformableRegistrationRadio = qt.QRadioButton('Deformable registration')
    self.noRegistrationRadio.setChecked(1)
    self.registrationModeGroup.addButton(self.noRegistrationRadio,1)
    self.registrationModeGroup.addButton(self.linearRegistrationRadio,2)
    self.registrationModeGroup.addButton(self.deformableRegistrationRadio,3)
    parametersFormLayout.addRow(qt.QLabel("Visualization mode"))
    parametersFormLayout.addRow("",self.noRegistrationRadio)
    parametersFormLayout.addRow("",self.linearRegistrationRadio)
    parametersFormLayout.addRow("",self.deformableRegistrationRadio)

    self.registrationModeGroup.connect('buttonClicked(int)',self.onVisualizationModeClicked)

    '''
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)
    '''

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    #self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    #self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    #self.onSelect()

    '''
    TODO:
     * improve GUI structure - separate parameters and visualization
     * improve interaction signal/slots

    '''

  def cleanup(self):
    pass

  def onSelect(self):
    # self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()
    pass

  def onApplyButton(self):
    logic = LabelRegistrationLogic()
    self.parameterNode = slicer.vtkMRMLScriptedModuleNode()

    # TODO: add checks for the selectors' content
    self.parameterNode.SetAttribute('FixedImageNodeID', self.fixedImageSelector.currentNode().GetID())
    self.parameterNode.SetAttribute('FixedLabelNodeID', self.fixedImageLabelSelector.currentNode().GetID())
    self.parameterNode.SetAttribute('MovingImageNodeID', self.movingImageSelector.currentNode().GetID())
    self.parameterNode.SetAttribute('MovingLabelNodeID', self.movingImageLabelSelector.currentNode().GetID())
    self.parameterNode.SetAttribute('OutputVolumeNodeID', self.outputImageSelector.currentNode().GetID())
    self.parameterNode.SetAttribute('AffineTransformNodeID', self.affineTransformSelector.currentNode().GetID())
    self.parameterNode.SetAttribute('BSplineTransformNodeID', self.bsplineTransformSelector.currentNode().GetID())
    logic.run(self.parameterNode)

    # resample moving volume
    # logic.resample(self.parameterNode)

    # configure the GUI
    logic.showResults(self.parameterNode)

    return

  def onVisualizationModeClicked(self,mode):
    movingVolume = slicer.mrmlScene.GetNodeByID(self.parameterNode.GetAttribute('MovingImageNodeID'))
    movingSurface = slicer.mrmlScene.GetNodeByID(self.parameterNode.GetAttribute('MovingLabelSurfaceID'))

    if mode == 1:
      movingVolume.SetAndObserveTransformNodeID('')
      movingSurface.SetAndObserveTransformNodeID('')
    if mode == 2:
      movingVolume.SetAndObserveTransformNodeID(self.parameterNode.GetAttribute('AffineTransformNodeID'))
      movingSurface.SetAndObserveTransformNodeID(self.parameterNode.GetAttribute('AffineTransformNodeID'))
    if mode == 3:
      movingVolume.SetAndObserveTransformNodeID(self.parameterNode.GetAttribute('BSplineTransformNodeID'))
      movingSurface.SetAndObserveTransformNodeID(self.parameterNode.GetAttribute('BSplineTransformNodeID'))
    return

#
# LabelRegistrationLogic
#

class LabelRegistrationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() == None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def run(self, parameterNode):
    """
    Run the actual algorithm
    """

    '''
    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False
    '''
    
    fixedLabelNodeID = parameterNode.GetAttribute('FixedLabelNodeID')
    movingLabelNodeID = parameterNode.GetAttribute('MovingLabelNodeID')
    outputVolumeNodeID = parameterNode.GetAttribute('OutputVolumeNodeID')
    affineTransformNode = slicer.mrmlScene.GetNodeByID(parameterNode.GetAttribute('AffineTransformNodeID'))
    bsplineTransformNode = slicer.mrmlScene.GetNodeByID(parameterNode.GetAttribute('BSplineTransformNodeID'))

    logging.info('Processing started')

    # crop the labels
    import SimpleITK as sitk
    import sitkUtils

    (bbMin,bbMax) = self.getBoundingBox(fixedLabelNodeID, movingLabelNodeID)

    print("Before preprocessing")

    fixedLabelDistanceMap = self.preProcessLabel(fixedLabelNodeID, bbMin, bbMax)
    parameterNode.SetAttribute('FixedLabelDistanceMapID',fixedLabelDistanceMap.GetID())
    fixedLabelSmoothed = slicer.util.getNode(slicer.mrmlScene.GetNodeByID(fixedLabelNodeID).GetName()+'-Smoothed')
    parameterNode.SetAttribute('FixedLabelSmoothedID',fixedLabelSmoothed.GetID())

    print('Fixed label processing done')

    movingLabelDistanceMap = self.preProcessLabel(movingLabelNodeID, bbMin, bbMax)
    parameterNode.SetAttribute('MovingLabelDistanceMapID',movingLabelDistanceMap.GetID())
    movingLabelSmoothed = slicer.util.getNode(slicer.mrmlScene.GetNodeByID(movingLabelNodeID).GetName()+'-Smoothed')
    parameterNode.SetAttribute('MovingLabelSmoothedID',movingLabelSmoothed.GetID())
    print('Moving label processing done')

    # run registration

    registrationParameters = {'fixedVolume':fixedLabelDistanceMap.GetID(), 'movingVolume':movingLabelDistanceMap.GetID(),'useRigid':True,'useAffine':True,'numberOfSamples':'10000','costMetric':'MSE','outputTransform':affineTransformNode.GetID()}
    slicer.cli.run(slicer.modules.brainsfit, None, registrationParameters, wait_for_completion=True)

    parameterNode.SetAttribute('AffineTransformNodeID',affineTransformNode.GetID())

    print('affineRegistrationCompleted!')

    registrationParameters = {'fixedVolume':fixedLabelDistanceMap.GetID(), 'movingVolume':movingLabelDistanceMap.GetID(),'useBSpline':True,'splineGridSize':'3,3,3','numberOfSamples':'10000','costMetric':'MSE','bsplineTransform':bsplineTransformNode.GetID(),'initialTransform':affineTransformNode.GetID()}
    slicer.cli.run(slicer.modules.brainsfit, None, registrationParameters, wait_for_completion=True)

    parameterNode.SetAttribute('BSplineTransformNodeID',bsplineTransformNode.GetID())

    print('bsplineRegistrationCompleted!')

    logging.info('Processing completed')

    return True

  def showResults(self,parameterNode):
    # duplicate moving volume

    self.makeSurfaceModels(parameterNode)

    volumesLogic = slicer.modules.volumes.logic()
    movingImageCloneID = parameterNode.GetAttribute('MovingImageCloneID')
    movingImageID = parameterNode.GetAttribute('MovingImageNodeID')
    fixedImageID = parameterNode.GetAttribute('FixedImageNodeID')
    movingImageNode = slicer.mrmlScene.GetNodeByID(movingImageID)

    if movingImageCloneID:
      slicer.mrmlScene.RemoveNode(slicer.mrmlScene.GetNodeByID(movingImageCloneID))
    
    movingImageClone = volumesLogic.CloneVolume(movingImageNode,'MovingImageCopy')
    parameterNode.SetAttribute('MovingImageCloneID',movingImageClone.GetID())

    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)

    sliceCompositeNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLSliceCompositeNode')
    sliceCompositeNodes.SetReferenceCount(sliceCompositeNodes.GetReferenceCount()-1)
    for i in range(sliceCompositeNodes.GetNumberOfItems()):
      scn = sliceCompositeNodes.GetItemAsObject(i)
      scn.SetForegroundVolumeID(fixedImageID)
      scn.SetBackgroundVolumeID(movingImageID)
    
    return

    # create surface model for the moving volume segmentation
    # apply transforms based on user input (none, affine, deformable)
    # (need to create another panel in the GUI for visualization)
    # enable transform visualization in-slice and 3d

  def makeSurfaceModels(self,parameterNode):
    fixedModel = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(fixedModel)
    parameters = {'inputImageName':parameterNode.GetAttribute('FixedLabelSmoothedID'),'outputMeshName':fixedModel.GetID()}
    slicer.cli.run(slicer.modules.quadedgesurfacemesher,None,parameters,wait_for_completion=True)
    parameterNode.SetAttribute('FixedLabelSurfaceID',fixedModel.GetID())
    fixedModel.GetDisplayNode().SetColor(0.9,0.9,0)

    movingModel = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(movingModel)
    parameters = {'inputImageName':parameterNode.GetAttribute('MovingLabelSmoothedID'),'outputMeshName':movingModel.GetID()}
    slicer.cli.run(slicer.modules.quadedgesurfacemesher,None,parameters,wait_for_completion=True)
    parameterNode.SetAttribute('MovingLabelSurfaceID',movingModel.GetID())
    movingModel.GetDisplayNode().SetColor(0,0.9,0.9)

    return

  def resample(self,parameterNode):
    resampleParameters = {'fixedVolume':fixedLabelDistanceMap.GetID(), 'movingVolume':movingLabelDistanceMap.GetID(),'useRigid':True,'useAffine':True,'numberOfSamples':'10000','costMetric':'MSE','outputTransform':affineTransformNode.GetID()}
    slicer.cli.run(slicer.modules.brainsfit, None, registrationParameters, wait_for_completion=True)

    parameterNode.SetAttribute('AffineTransformNodeID',affineTransformNode.GetID())



  def getBoundingBox(self,fixedLabelNodeID,movingLabelNodeID):

    ls = sitk.LabelStatisticsImageFilter()

    fixedLabelNode = slicer.mrmlScene.GetNodeByID(fixedLabelNodeID)
    movingLabelNode = slicer.mrmlScene.GetNodeByID(movingLabelNodeID)

    fixedLabelAddress = sitkUtils.GetSlicerITKReadWriteAddress(fixedLabelNode.GetName())
    movingLabelAddress = sitkUtils.GetSlicerITKReadWriteAddress(movingLabelNode.GetName())

    fixedLabelImage = sitk.ReadImage(fixedLabelAddress)
    movingLabelImage = sitk.ReadImage(movingLabelAddress)

    cast = sitk.CastImageFilter()
    cast.SetOutputPixelType(2)
    unionLabelImage = (cast.Execute(fixedLabelImage) + cast.Execute(movingLabelImage)) > 0
    unionLabelImage = cast.Execute(unionLabelImage)

    ls.Execute(unionLabelImage,unionLabelImage)
    bb = ls.GetBoundingBox(1)
    print(str(bb))

    size = unionLabelImage.GetSize()
    bbMin = (max(0,bb[0]-30),max(0,bb[2]-30),max(0,bb[4]-5))
    bbMax = (size[0]-min(size[0],bb[1]+30),size[1]-min(size[1],bb[3]+30),size[2]-(min(size[2],bb[5]+5)))

    return (bbMin,bbMax)

  def preProcessLabel(self,labelNodeID,bbMin,bbMax):

    print('Label node ID: '+labelNodeID)

    labelNode = slicer.util.getNode(labelNodeID)

    labelNodeAddress = sitkUtils.GetSlicerITKReadWriteAddress(labelNode.GetName())

    print('Label node address: '+str(labelNodeAddress))

    labelImage = sitk.ReadImage(labelNodeAddress)

    print('Read image: '+str(labelImage))

    crop = sitk.CropImageFilter()
    crop.SetLowerBoundaryCropSize(bbMin)
    crop.SetUpperBoundaryCropSize(bbMax)
    croppedImage = crop.Execute(labelImage)

    print('Cropped image done: '+str(croppedImage))

    croppedLabelName = labelNode.GetName()+'-Cropped'
    sitkUtils.PushToSlicer(croppedImage,croppedLabelName,overwrite=True)
    print('Cropped volume pushed')

    croppedLabel = slicer.util.getNode(croppedLabelName)

    print('Smoothed image done')

    smoothLabelName = labelNode.GetName()+'-Smoothed'
    smoothLabel = self.createVolumeNode(smoothLabelName)

    # smooth the labels
    smoothingParameters = {'inputImageName':croppedLabel.GetID(), 'outputImageName':smoothLabel.GetID()}
    print(str(smoothingParameters))
    cliNode = slicer.cli.run(slicer.modules.segmentationsmoothing, None, smoothingParameters, wait_for_completion = True)

    # crop the bounding box
    
    '''
    TODO:
     * output volume node probably not needed here
     * intermediate nodes should probably be hidden
    '''

    dt = sitk.SignedMaurerDistanceMapImageFilter()
    dt.SetSquaredDistance(False)
    distanceMapName = labelNode.GetName()+'-DistanceMap'
    print('Reading smoothed image: '+smoothLabel.GetID())
    smoothLabelAddress = sitkUtils.GetSlicerITKReadWriteAddress(smoothLabel.GetName())    
    smoothLabelImage = sitk.ReadImage(smoothLabelAddress)
    print(smoothLabelAddress)
    distanceImage = dt.Execute(smoothLabelImage)
    sitkUtils.PushToSlicer(distanceImage, distanceMapName, overwrite=True)

    return slicer.util.getNode(distanceMapName)

  def createVolumeNode(self,name):
    import sitkUtils
    node = sitkUtils.CreateNewVolumeNode(name,overwrite=True)
    storageNode = slicer.vtkMRMLNRRDStorageNode()
    slicer.mrmlScene.AddNode(storageNode)
    node.SetAndObserveStorageNodeID(storageNode.GetID())
    return node

class LabelRegistrationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_LabelRegistration1()

  def test_LabelRegistration1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = LabelRegistrationLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')


    '''

    TODO:
     * add main() so that registration could be run from command line

    '''
