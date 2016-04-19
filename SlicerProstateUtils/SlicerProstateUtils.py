import slicer


class SlicerProstateUtilsClass(object):

  def __init__(self):
    pass


class SlicerProstateUtils:
  """
  This class is the 'hook' for slicer to detect and recognize the plugin
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "SlicerProstate Utils"
    parent.categories = ["Developer Tools.Utils"]
    parent.contributors = ["Christian Herz (SPL)"]
    parent.helpText = """

    No module interface here.
    """
    parent.acknowledgementText = """
    These SlicerProstate utils were developed by
    Christian Herz, SPL
    """

    try:
      slicer.modules.slicerprostate
    except AttributeError:
      slicer.modules.slicerprostate = {}
    slicer.modules.slicerprostate['SlicerProstateUtils'] = SlicerProstateUtilsClass