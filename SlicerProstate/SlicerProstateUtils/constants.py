import qt


class DICOMTAGS:

  PATIENT_NAME          = '0010,0010'
  PATIENT_ID            = '0010,0020'
  PATIENT_BIRTH_DATE    = '0010,0030'
  SERIES_DESCRIPTION    = '0008,103E'
  SERIES_NUMBER         = '0020,0011'
  STUDY_DATE            = '0008,0020'
  STUDY_ID              = '0020,0010'
  STUDY_TIME            = '0008,0030'
  ACQUISITION_TIME      = '0008,0032'


class COLOR:

  RED = qt.QColor(qt.Qt.red)
  YELLOW = qt.QColor(qt.Qt.yellow)
  GREEN = qt.QColor(qt.Qt.darkGreen)
  GRAY = qt.QColor(qt.Qt.gray)


class STYLE:

  WHITE_BACKGROUND            = 'background-color: rgb(255,255,255)'
  LIGHT_GRAY_BACKGROUND       = 'background-color: rgb(230,230,230)'
  ORANGE_BACKGROUND           = 'background-color: rgb(255,102,0)'
  YELLOW_BACKGROUND           = 'background-color: yellow;'
  GREEN_BACKGROUND            = 'background-color: green;'
  GRAY_BACKGROUND             = 'background-color: gray;'
  RED_BACKGROUND              = 'background-color: red;'


class FileExtension(object):

  TXT = ".TXT"
  NRRD = ".nrrd"
  FCSV = ".fcsv"
  H5 = ".h5"
  VTK = ".vtk"