import vtk

class SlicerProstateEvents(object):

  IncomingDataSkippedEvent = vtk.vtkCommand.UserEvent + 200
  IncomingDataCanceledEvent = vtk.vtkCommand.UserEvent + 201
  IncomingDataReceiveFinishedEvent = vtk.vtkCommand.UserEvent + 202
  IncomingFileCountChangedEvent = vtk.vtkCommand.UserEvent + 203

  StatusChangedEvent = vtk.vtkCommand.UserEvent + 203

  RatingWindowClosedEvent = vtk.vtkCommand.UserEvent + 204