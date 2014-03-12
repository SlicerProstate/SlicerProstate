#include "itkImageFileWriter.h"
#include "itkImageDuplicator.h"
#include "itkMetaDataObject.h"
#include "itkLevenbergMarquardtOptimizer.h"
#include "itkArray.h"


#include "itkPluginUtilities.h"
//#include "lmcurve.h"

#include "DWModelingCLP.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "itkImageRegionConstIteratorWithIndex.h"

//double f(double t, const double *p){
//  return p[1]*exp(p[0]*t);
//}

//int fit_exp(double *par, int m_dat, double *t, double *y);

#define SimpleAttributeGetMethodMacro(name, key, type)     \
type Get##name(itk::MetaDataDictionary& dictionary)           \
{\
  type value = type(); \
  if (dictionary.HasKey(key))\
    {\
    /* attributes stored as strings */ \
    std::string valueString; \
    itk::ExposeMetaData(dictionary, key, valueString);  \
    std::stringstream valueStream(valueString); \
    valueStream >> value; \
    }\
  else\
    {\
    itkGenericExceptionMacro("Missing attribute '" key "'.");\
    }\
  return value;\
}

//SimpleAttributeGetMethodMacro(EchoTime, "MultiVolume.DICOM.EchoTime", float);
SimpleAttributeGetMethodMacro(RepetitionTime, "MultiVolume.DICOM.RepetitionTime",float);
SimpleAttributeGetMethodMacro(FlipAngle, "MultiVolume.DICOM.FlipAngle", float);

std::vector<float> GetBvalues(itk::MetaDataDictionary& dictionary)
{
  std::vector<float> bValues;

  if (dictionary.HasKey("MultiVolume.FrameIdentifyingDICOMTagName"))
    {
    std::string tag;
    itk::ExposeMetaData(dictionary, "MultiVolume.FrameIdentifyingDICOMTagName", tag);
    if (dictionary.HasKey("MultiVolume.FrameLabels"))
      {
      // Acquisition parameters stored as text, FrameLabels are comma separated
      std::string frameLabelsString;
      itk::ExposeMetaData(dictionary, "MultiVolume.FrameLabels", frameLabelsString);
      std::stringstream frameLabelsStream(frameLabelsString);
      if (tag == "B-value")
        {
        float t;
        while (frameLabelsStream >> t)
          {
          bValues.push_back(t);
          frameLabelsStream.ignore(1); // skip the comma
          }
        }
      else
        {
        itkGenericExceptionMacro("Unrecognized frame identifying DICOM tag name " << tag);
        }
      }
    else
      {
      itkGenericExceptionMacro("Missing attribute 'MultiVolume.FrameLabels'.")
      }
    }
  else
    {
    itkGenericExceptionMacro("Missing attribute 'MultiVolume.FrameIdentifyingDICOMTagName'.");
    }
  
  return bValues;
}


class ExpDecayCostFunction: public itk::MultipleValuedCostFunction
{
public:
  typedef ExpDecayCostFunction                    Self;
  typedef itk::MultipleValuedCostFunction   Superclass;
  typedef itk::SmartPointer<Self>           Pointer;
  typedef itk::SmartPointer<const Self>     ConstPointer;
  itkNewMacro( Self );
        
  enum { SpaceDimension =  3 };
  unsigned int RangeDimension; 

  typedef Superclass::ParametersType              ParametersType;
  typedef Superclass::DerivativeType              DerivativeType;
  typedef Superclass::MeasureType                 MeasureType, ArrayType;
  typedef Superclass::ParametersValueType         ValueType;
		      
        
  ExpDecayCostFunction()
  {
  }
        
  void SetY (const float* y, int sz) //Self signal Y
  {    
    Y.set_size (sz);
    for (int i = 0; i < sz; ++i)
      Y[i] = y[i];
    //std::cout << "Cv: " << Y << std::endl;
  }
        
  void SetX (const float* x, int sz) //Self signal X
  {
    X.set_size (sz);
    for( int i = 0; i < sz; ++i )
      X[i] = x[i];
    //std::cout << "Time: " << X << std::endl;
  }

  ArrayType GetX(){
    return X;
  }

  ArrayType GetY(){
    return Y;
  }
        
  MeasureType GetFittedValue( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);
    for(int i=0;i<measure.size();i++)
      {
      measure[i] = exp(-1.*X[i]*parameters[0])*parameters[1];
      }
    return measure;
  }

  MeasureType GetValue( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);

    for(int i=0;i<measure.size();i++)
      {
      measure[i] = Y[i]-exp(-1.*X[i]*parameters[0])*parameters[1];
      }
           
    return measure; 
  }
        
  //Not going to be used
  void GetDerivative( const ParametersType & /* parameters*/,
                      DerivativeType  & /*derivative*/ ) const
  {   
  }
        
  unsigned int GetNumberOfParameters(void) const
  {
    return 2;
  }
       
  void SetNumberOfValues(unsigned int nValues)
    {
    RangeDimension = nValues;
    }

  unsigned int GetNumberOfValues(void) const
  {
    return RangeDimension;
  }
        
protected:
  virtual ~ExpDecayCostFunction(){}
private:
        
  ArrayType X, Y;
        
  ArrayType Exponential(ArrayType X) const
  {
    ArrayType Z;
    Z.set_size(X.size());
    for (unsigned int i=0; i<X.size(); i++)
      {
      Z[i] = exp(X(i));
      }
    return Z;
  };
        
  int constraintFunc(ValueType x) const
  {
    if (x<0||x>1)
      return 1;
    else
      return 0;
            
  };
        
        
};

class MultiExpDecayCostFunction: public itk::MultipleValuedCostFunction
{
public:
  typedef MultiExpDecayCostFunction                    Self;
  typedef itk::MultipleValuedCostFunction   Superclass;
  typedef itk::SmartPointer<Self>           Pointer;
  typedef itk::SmartPointer<const Self>     ConstPointer;
  itkNewMacro( Self );
        
  enum { SpaceDimension =  3 };
  unsigned int RangeDimension; 

  typedef Superclass::ParametersType              ParametersType;
  typedef Superclass::DerivativeType              DerivativeType;
  typedef Superclass::MeasureType                 MeasureType, ArrayType;
  typedef Superclass::ParametersValueType         ValueType;
		      
        
  MultiExpDecayCostFunction()
  {
  }
        
  void SetY (const float* y, int sz) //Self signal Y
  {    
    Y.set_size (sz);
    for (int i = 0; i < sz; ++i)
      Y[i] = y[i];
    //std::cout << "Cv: " << Y << std::endl;
  }
        
  void SetX (const float* x, int sz) //Self signal X
  {
    X.set_size (sz);
    for( int i = 0; i < sz; ++i )
      X[i] = x[i];
    //std::cout << "Time: " << X << std::endl;
  }

  ArrayType GetX(){
    return X;
  }

  ArrayType GetY(){
    return Y;
  }
        
  MeasureType GetFittedValue( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);

    float scale = parameters[0],
          fraction = parameters[1],
          diffusion = parameters[2],
          perfusion = parameters[3];

    for(int i=0;i<measure.size();i++)
      {
      measure[i] = 
        scale*((1-fraction)*exp(-1.*X[i]*diffusion)+fraction*exp(-1.*X[i]*perfusion));
      }
    return measure;
  }

  MeasureType GetValue( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);

    float scale = parameters[0],
          fraction = parameters[1],
          diffusion = parameters[2],
          perfusion = parameters[3];

    for(int i=0;i<measure.size();i++)
      {
      measure[i] = 
        Y[i]-scale*((1-fraction)*exp(-1.*X[i]*diffusion)+fraction*exp(-1.*X[i]*perfusion));
      }
           
    return measure; 
  }
        
  //Not going to be used
  void GetDerivative( const ParametersType & /* parameters*/,
                      DerivativeType  & /*derivative*/ ) const
  {   
  }
        
  unsigned int GetNumberOfParameters(void) const
  {
    return 4;
  }
       
  void SetNumberOfValues(unsigned int nValues)
    {
    RangeDimension = nValues;
    }

  unsigned int GetNumberOfValues(void) const
  {
    return RangeDimension;
  }
        
protected:
  virtual ~MultiExpDecayCostFunction(){}
private:
        
  ArrayType X, Y;
        
  ArrayType Exponential(ArrayType X) const
  {
    ArrayType Z;
    Z.set_size(X.size());
    for (unsigned int i=0; i<X.size(); i++)
      {
      Z[i] = exp(X(i));
      }
    return Z;
  };
        
  int constraintFunc(ValueType x) const
  {
    if (x<0||x>1)
      return 1;
    else
      return 0;
            
  };
        
        
};


// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
int main( int argc, char * argv[])
{
  PARSE_ARGS;

  const   unsigned int VectorVolumeDimension = 3;
  typedef float                                                 VectorVolumePixelType;
  typedef itk::VectorImage<VectorVolumePixelType, VectorVolumeDimension> VectorVolumeType;
  typedef VectorVolumeType::RegionType              VectorVolumeRegionType;
  typedef itk::ImageFileReader<VectorVolumeType>             VectorVolumeReaderType;

  typedef unsigned char                                        MaskVolumePixelType;
  typedef float                                                MapVolumePixelType;
  typedef itk::Image<MaskVolumePixelType, 3>                   MaskVolumeType;
  typedef itk::Image<MapVolumePixelType, 3>                    MapVolumeType;
  typedef itk::ImageFileReader<MaskVolumeType>                 MaskVolumeReaderType;
  typedef itk::ImageFileWriter<MapVolumeType>                  MapWriterType;
  typedef itk::ImageFileWriter<VectorVolumeType>               FittedVolumeWriterType;

  typedef itk::Image<float,VectorVolumeDimension> OutputVolumeType;
  typedef itk::ImageDuplicator<VectorVolumeType> DuplicatorType;
  typedef itk::ImageFileWriter< MapVolumeType> MapVolumeWriterType;

  typedef itk::ImageRegionIterator<VectorVolumeType> VectorVolumeIteratorType;
  typedef itk::ImageRegionConstIterator<MaskVolumeType> MaskVolumeIteratorType;
  typedef itk::ImageRegionIterator<MapVolumeType> MapVolumeIteratorType;
  
  //Read VectorVolume
  VectorVolumeReaderType::Pointer multiVolumeReader 
    = VectorVolumeReaderType::New();
  multiVolumeReader->SetFileName(imageName.c_str() );
  multiVolumeReader->Update();
  VectorVolumeType::Pointer inputVectorVolume = multiVolumeReader->GetOutput();

  // Read mask
  MaskVolumeType::Pointer maskVolume;
  if(maskName != ""){
    MaskVolumeReaderType::Pointer maskReader = MaskVolumeReaderType::New();
    maskReader->SetFileName(maskName.c_str());
    maskReader->Update();
    maskVolume = maskReader->GetOutput();
  } else {
    maskVolume = MaskVolumeType::New();
    maskVolume->SetRegions(inputVectorVolume->GetLargestPossibleRegion());
    maskVolume->CopyInformation(inputVectorVolume);
    maskVolume->Allocate();
    maskVolume->FillBuffer(1);
  }

  //Look for tags representing the acquisition parameters
  //
  //

  // Trigger times
  std::vector<float> bValues;
  float *bValuesPtr;
  try
    {
    bValues = GetBvalues(inputVectorVolume->GetMetaDataDictionary());
    bValuesPtr = new float[bValues.size()];
    for(int i=0;i<bValues.size();i++)
      bValuesPtr[i] = bValues[i];
    }
  catch (itk::ExceptionObject &exc)
    {
    itkGenericExceptionMacro(<< exc.GetDescription() 
            << " Image " << imageName 
            << " does not contain sufficient attributes to support algorithms.");
    return EXIT_FAILURE;
    }

  MapVolumeType::Pointer diffusionMap = MapVolumeType::New();
  diffusionMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  diffusionMap->Allocate();
  diffusionMap->FillBuffer(0);
  diffusionMap->CopyInformation(maskVolume);
  diffusionMap->FillBuffer(0);

  MapVolumeType::Pointer perfusionMap = MapVolumeType::New();
  perfusionMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  perfusionMap->Allocate();
  perfusionMap->FillBuffer(0);
  perfusionMap->CopyInformation(maskVolume);
  perfusionMap->FillBuffer(0);

  MapVolumeType::Pointer perfusionFractionMap = MapVolumeType::New();
  perfusionFractionMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  perfusionFractionMap->Allocate();
  perfusionFractionMap->FillBuffer(0);
  perfusionFractionMap->CopyInformation(maskVolume);
  perfusionFractionMap->FillBuffer(0);

  MapVolumeType::Pointer rsqrMap = MapVolumeType::New();
  rsqrMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  rsqrMap->Allocate();
  rsqrMap->FillBuffer(0);
  rsqrMap->CopyInformation(maskVolume);
  rsqrMap->FillBuffer(0);

  DuplicatorType::Pointer dup = DuplicatorType::New();
  dup->SetInputImage(inputVectorVolume);
  dup->Update();
  VectorVolumeType::Pointer fittedVolume = dup->GetOutput();
  VectorVolumeType::PixelType zero = VectorVolumeType::PixelType(bValues.size());
  for(int i=0;i<bValues.size();i++)
    zero[i] = 0;
  fittedVolume->FillBuffer(zero);

  VectorVolumeIteratorType vvIt(inputVectorVolume, inputVectorVolume->GetLargestPossibleRegion());
  MaskVolumeIteratorType mvIt(maskVolume, maskVolume->GetLargestPossibleRegion());
  MapVolumeIteratorType diffIt(diffusionMap, diffusionMap->GetLargestPossibleRegion());
  MapVolumeIteratorType perfIt(perfusionMap, perfusionMap->GetLargestPossibleRegion());
  MapVolumeIteratorType perfFracIt(perfusionFractionMap, perfusionFractionMap->GetLargestPossibleRegion());
  MapVolumeIteratorType rsqrIt(rsqrMap, rsqrMap->GetLargestPossibleRegion());
  VectorVolumeIteratorType fittedIt(fittedVolume, fittedVolume->GetLargestPossibleRegion());

  itk::LevenbergMarquardtOptimizer::Pointer optimizer = itk::LevenbergMarquardtOptimizer::New();
  MultiExpDecayCostFunction::Pointer costFunction = MultiExpDecayCostFunction::New();
  MultiExpDecayCostFunction::ParametersType initialValue = MultiExpDecayCostFunction::ParametersType(4);
  unsigned numValues = inputVectorVolume->GetNumberOfComponentsPerPixel();
  costFunction->SetNumberOfValues(numValues);

  initialValue[0] = 5000; // use b0
  initialValue[1] = 0.5; // 0.7
  initialValue[2] = 0.001; // go lower 4 times
  initialValue[3] = 0.002; // 

  int cnt = 0;
  vvIt.GoToBegin();mvIt.GoToBegin();rsqrIt.GoToBegin();
  perfIt.GoToBegin();diffIt.GoToBegin();perfFracIt.GoToBegin();fittedIt.GoToBegin();
  for(;!diffIt.IsAtEnd();++vvIt,++mvIt,++perfIt,++diffIt,++perfFracIt,++fittedIt,++rsqrIt){
      VectorVolumeType::PixelType vectorVoxel = vvIt.Get();
      VectorVolumeType::PixelType fittedVoxel(vectorVoxel.GetSize());
      for(int i=0;i<fittedVoxel.GetSize();i++)
       fittedVoxel[i] = 0;

      if(mvIt.Get() && vectorVoxel[0]){
        costFunction->SetX(bValuesPtr, numValues);
        costFunction->SetY(const_cast<float*>(vectorVoxel.GetDataPointer()),numValues);
        MultiExpDecayCostFunction::MeasureType temp = costFunction->GetValue(initialValue);

        optimizer->UseCostFunctionGradientOff();
        optimizer->SetCostFunction(costFunction);

        itk::LevenbergMarquardtOptimizer::InternalOptimizerType *vnlOptimizer = optimizer->GetOptimizer();
        vnlOptimizer->set_f_tolerance(1e-4f);
        vnlOptimizer->set_g_tolerance(1e-4f);
        vnlOptimizer->set_x_tolerance(1e-5f);
        vnlOptimizer->set_epsilon_function(1e-9f);
        vnlOptimizer->set_max_function_evals(200);

        try {
          optimizer->SetInitialPosition(initialValue);
          optimizer->StartOptimization();
        } catch(itk::ExceptionObject &e) {
            std::cout << " Exception caught: " << e << std::endl;

        }

        itk::LevenbergMarquardtOptimizer::ParametersType finalPosition;
        finalPosition = optimizer->GetCurrentPosition();

        MultiExpDecayCostFunction::MeasureType fittedMeasure = 
          costFunction->GetFittedValue(finalPosition);
        for(int i=0;i<fittedVoxel.GetSize();i++){
          fittedVoxel[i] = fittedMeasure[i];
        }

        perfFracIt.Set(finalPosition[1]);
        diffIt.Set(finalPosition[2]*1e+6);
        perfIt.Set(finalPosition[3]*1e+6);

        // initialize the rsqr map
        // see PkModeling/CLI/itkConcenttationToQuantitativeImageFilter.hxx:452
        {
          MultiExpDecayCostFunction::MeasureType residuals = costFunction->GetValue(optimizer->GetCurrentPosition());
          double rms = optimizer->GetOptimizer()->get_end_error();
          double SSerr = rms*rms*vectorVoxel.GetSize();
          double sumSquared = 0.0;
          double sum = 0.0;
          for (unsigned int i=0; i < vectorVoxel.GetSize(); ++i){
            sum += vectorVoxel[i];
            sumSquared += (vectorVoxel[i]*vectorVoxel[i]);
          }
          double SStot = sumSquared - sum*sum/(double)vectorVoxel.GetSize();
     
          double rSquared = 1.0 - (SSerr / SStot);
          rsqrIt.Set(rSquared);
        }

        fittedIt.Set(fittedVoxel);
      }
  }


  if(diffusionMapFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(diffusionMap);
    writer->SetFileName(diffusionMapFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }
  if(perfusionMapFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(perfusionMap);
    writer->SetFileName(perfusionMapFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }
  if(perfusionFractionMapFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(perfusionFractionMap);
    writer->SetFileName(perfusionFractionMapFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }
  if(rsqrVolumeFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(rsqrMap);
    writer->SetFileName(rsqrVolumeFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }
  if(fittedVolumeFileName.size()){
    FittedVolumeWriterType::Pointer writer = FittedVolumeWriterType::New();
    fittedVolume->SetMetaDataDictionary(inputVectorVolume->GetMetaDataDictionary());
    writer->SetInput(fittedVolume);
    writer->SetFileName(fittedVolumeFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }

  return EXIT_SUCCESS;
}
