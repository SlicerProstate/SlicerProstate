cmake_minimum_required(VERSION 2.8.9)

project(ProstateIGT)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/ProstateIGT")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Andrey Fedorov (BWH)")
set(EXTENSION_DESCRIPTION "This is a collection of modules in support of prostate image guided therapy clinical research.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/ProstateIGT.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/ProstateIGT/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(QuadEdgeSurfaceMesher)
add_subdirectory(SegmentationSmoothing)
add_subdirectory(DistanceMapBasedRegistration)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
