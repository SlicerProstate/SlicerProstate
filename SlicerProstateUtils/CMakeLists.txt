#-----------------------------------------------------------------------------
set(MODULE_NAME SlicerProstateUtils)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}/__init__.py
  ${MODULE_NAME}/mixins.py
  ${MODULE_NAME}/helpers.py
  ${MODULE_NAME}/constants.py
  ${MODULE_NAME}/decorators.py
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