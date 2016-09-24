import vtk, slicer

class SlicerProstateEvents(object):

  NewImageDataReceivedEvent = vtk.vtkCommand.UserEvent + 100
  NewFileIndexedEvent = vtk.vtkCommand.UserEvent + 101

  IncomingDataSkippedEvent = vtk.vtkCommand.UserEvent + 200
  IncomingDataCanceledEvent = vtk.vtkCommand.UserEvent + 201
  IncomingDataReceiveFinishedEvent = vtk.vtkCommand.UserEvent + 202
  IncomingFileCountChangedEvent = vtk.vtkCommand.UserEvent + 203
  DICOMReceiverStartedEvent = vtk.vtkCommand.UserEvent + 204
  DICOMReceiverStoppedEvent = vtk.vtkCommand.UserEvent + 205

  StatusChangedEvent = vtk.vtkCommand.UserEvent + 206

  RatingWindowClosedEvent = vtk.vtkCommand.UserEvent + 304

  DownloadCanceledEvent = vtk.vtkCommand.UserEvent + 401
  DownloadFinishedEvent = vtk.vtkCommand.UserEvent + 402
  DownloadFailedEvent = vtk.vtkCommand.UserEvent + 403

  CursorPositionModifiedEvent = slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent