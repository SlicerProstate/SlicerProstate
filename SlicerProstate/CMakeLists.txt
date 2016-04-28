#-----------------------------------------------------------------------------
set(MODULE_NAME SlicerProstate)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}Utils/__init__.py
  ${MODULE_NAME}Utils/mixins.py
  ${MODULE_NAME}Utils/helpers.py
  ${MODULE_NAME}Utils/constants.py
  ${MODULE_NAME}Utils/decorators.py
  ${MODULE_NAME}Utils/events.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/icon-star-filled.png
  Resources/Icons/icon-star-unfilled.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  )