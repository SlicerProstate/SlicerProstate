#include <iostream>

#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkQuadEdgeMesh.h"
#include "itkTriangleCell.h"

#include "itkBinaryThresholdImageFilter.h"
#include "itkBinaryMask3DMeshSource.h"
#include "itkQuadEdgeMeshDecimationCriteria.h"
#include "itkSquaredEdgeLengthDecimationQuadEdgeMeshFilter.h"

#include "itkMeshFileWriter.h"

#include "vtkPLYWriter.h"
#include "vtkSmartPointer.h"
#include "vtkPolyData.h"

#include "itkTriangleMeshToBinaryImageFilter.h"
#include "itkImageDuplicator.h"

#include <QuadEdgeSurfaceMesherCLP.h>

const unsigned int Dimension = 3;
typedef double PixelType;

typedef itk::Image<PixelType,   Dimension>   ImageType; // float to use uniform for all images
typedef itk::ImageFileReader<ImageType> ReaderType;
typedef itk::BinaryThresholdImageFilter<ImageType,ImageType> ThreshType;

typedef itk::QuadEdgeMesh < double,3 > MeshType;

typedef MeshType::PointsContainer::Iterator PointsIterator;
typedef MeshType::CellsContainer::Iterator CellsIterator;

typedef itk::MeshFileWriter<MeshType> MeshWriterType;
  
typedef itk::BinaryMask3DMeshSource< ImageType, MeshType >   MeshSourceType;
typedef itk::TriangleMeshToBinaryImageFilter<MeshType,ImageType> Mesh2ImageType;

vtkSmartPointer<vtkPolyData> ITKMesh2PolyData(MeshType::Pointer);
void PrintSurfaceStatistics(vtkPolyData*);
void WriteMesh(MeshType::Pointer, const char*);
void MeshLPStoRAS(MeshType::Pointer mesh);

int main(int argc, char **argv){
  PARSE_ARGS;

  ImageType::Pointer mask;

  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName(inputImageName.c_str());
  
  ThreshType::Pointer thresh = ThreshType::New();
  thresh->SetInput(reader->GetOutput());
  thresh->SetLowerThreshold(labelId);
  thresh->SetUpperThreshold(labelId);
  thresh->SetInsideValue(1);  
  thresh->Update();

  MeshSourceType::Pointer meshSource = MeshSourceType::New();

  meshSource->SetInput( thresh->GetOutput());
  meshSource->SetObjectValue(1);
  meshSource->Update();

  std::cout << "MC surface points: " << meshSource->GetNumberOfNodes() << std::endl;
  std::cout << "MC surface cells: " << meshSource->GetNumberOfCells() << std::endl;

  // decimate the mesh
  typedef itk::NumberOfFacesCriterion< MeshType > CriterionType;
  typedef itk::SquaredEdgeLengthDecimationQuadEdgeMeshFilter< 
    MeshType, MeshType, CriterionType > DecimationType;

  CriterionType::Pointer criterion = CriterionType::New();
  criterion->SetTopologicalChange( false );
  std::cout << "Target number of cells after decimation: " << 
    (unsigned) (decimationConst*meshSource->GetNumberOfCells()) << std::endl;
  criterion->SetNumberOfElements( unsigned(decimationConst*meshSource->GetNumberOfCells()));
  
  MeshType::Pointer mcmesh = meshSource->GetOutput();
 
  DecimationType::Pointer decimate = DecimationType::New();
  decimate->SetInput( meshSource->GetOutput() );
  decimate->SetCriterion( criterion );
  decimate->Update();

  MeshType::Pointer dMesh = decimate->GetOutput();

  MeshLPStoRAS(dMesh);

  std::cout << "Decimation complete" << std::endl;
  std::cout << "Decimated surface points: " << dMesh->GetPoints()->Size() << std::endl;
  std::cout << "Decimated surface cells: " << dMesh->GetCells()->Size() << std::endl;
  WriteMesh(dMesh, outputMeshName.c_str());

  return EXIT_SUCCESS;

}


void MeshLPStoRAS(MeshType::Pointer mesh){
  PointsIterator pIt = mesh->GetPoints()->Begin();
  PointsIterator pEnd = mesh->GetPoints()->End();
  unsigned i = 0;

  while(pIt!=pEnd){
    MeshType::PointType p = pIt.Value();
    p[0] *= -1.;
    p[1] *= -1;
    mesh->SetPoint(i, p);
    pIt++;
    i++;
  }
}

vtkSmartPointer<vtkPolyData> ITKMesh2PolyData(MeshType::Pointer mesh){
  vtkSmartPointer<vtkPolyData> surface = vtkSmartPointer<vtkPolyData>::New();
  vtkSmartPointer<vtkPoints> surfacePoints = vtkSmartPointer<vtkPoints>::New();

  surfacePoints->SetNumberOfPoints(mesh->GetPoints()->Size());
  
  PointsIterator pIt = mesh->GetPoints()->Begin(), pItEnd = mesh->GetPoints()->End();
  CellsIterator cIt = mesh->GetCells()->Begin(), cItEnd = mesh->GetCells()->End();

  while(pIt!=pItEnd){
    MeshType::PointType pt = pIt->Value();
    surfacePoints->SetPoint(pIt->Index(), pt[0], pt[1], pt[2]);
    ++pIt;
  }

  surface->SetPoints(surfacePoints);
  surface->Allocate();

  while(cIt!=cItEnd){
    MeshType::CellType *cell = cIt->Value();
    MeshType::CellType::PointIdIterator pidIt = cell->PointIdsBegin(); 
    vtkIdType cIds[3];
    cIds[0] = *pidIt;
    cIds[1] = *(pidIt+1);
    cIds[2] = *(pidIt+2);
    surface->InsertNextCell(VTK_TRIANGLE, 3, cIds);

    ++cIt;
  }
  return surface;
}

void WriteMesh(MeshType::Pointer mesh, const char* fname){
  vtkSmartPointer<vtkPolyData> vtksurf = ITKMesh2PolyData(mesh);
  vtkSmartPointer<vtkPLYWriter> pdw = vtkSmartPointer<vtkPLYWriter>::New();
  pdw->SetFileName(fname);
  pdw->SetInputData(vtksurf);
  pdw->Update();
}
