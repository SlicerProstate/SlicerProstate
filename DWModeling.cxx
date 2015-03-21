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
      if (tag == "GE.B-value")
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
        
  MeasureType GetFittedVector( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);

    float scale = parameters[0],
          fraction = parameters[1],
          slowDiff = parameters[2],
          fastDiff = parameters[3];

    for(int i=0;i<measure.size();i++)
      {
      measure[i] = 
        scale*((1-fraction)*exp(-1.*X[i]*slowDiff)+fraction*exp(-1.*X[i]*fastDiff));
      }
    return measure;
  }

  float GetFittedValue(const ParametersType & parameters, float x) const
  {
    float scale = parameters[0],
          fraction = parameters[1],
          slowDiff = parameters[2],
          fastDiff = parameters[3];

      float measure = 
        scale*((1-fraction)*exp(-1.*x*slowDiff)+fraction*exp(-1.*x*fastDiff));
      
    return measure;
  }

  MeasureType GetValue( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);

    float scale = parameters[0],
          fraction = parameters[1],
          slowDiff = parameters[2],
          fastDiff = parameters[3];

    for(int i=0;i<measure.size();i++)
      {
      measure[i] = 
        Y[i]-scale*((1-fraction)*exp(-1.*X[i]*slowDiff)+fraction*exp(-1.*X[i]*fastDiff));
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

// https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
void OnlineVariance(itk::MultipleValuedCostFunction::MeasureType &values,
    double &mean, double &SD){
  double n = 0, M2 = 0;
     
  for(unsigned int i=0;i<values.GetSize();i++){
    double x = values[i];
    n++;
    double delta = x - mean;
    mean = mean + delta/n;
    M2 = M2 + delta*(x - mean);
  }
  SD = sqrt(M2/(n-1));
}

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
  
  if(bValuesToInclude.size() and bValuesToExclude.size()){
    std::cerr << "ERROR: Either inclusion or exclusion b-values list can be specified, not both!" << std::endl;
    return -1;
  }

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
  // list of b-values to be passed to the optimizer
  float *bValuesPtr, *imageValuesPtr;
  // "true" for the b-value and measurement pair to be used in fitting
  bool *bValuesMask;
  int bValuesTotal, bValuesSelected;
  try {

    bValues = GetBvalues(inputVectorVolume->GetMetaDataDictionary());
    bValuesTotal = bValues.size();
    bValuesMask = new bool[bValuesTotal];

    // if the inclusion list is non-empty, use only the values requested by the
    // user
    if(bValuesToInclude.size()){
      memset(bValuesMask,false,sizeof(bool)*bValuesTotal);
      bValuesSelected = 0;
      for(int i=0;i<bValuesTotal;i++){
        if(std::find(bValuesToInclude.begin(), bValuesToInclude.end(), bValues[i]) 
            != bValuesToInclude.end()){
          bValuesMask[i] = true;
          bValuesSelected++;
        }
      }
    // if the exclusion list is non-empty, do not use the values requested by the
    // user
    } else if(bValuesToExclude.size()) {
      memset(bValuesMask,true,sizeof(bool)*bValuesTotal);
      bValuesSelected = bValuesTotal;
      for(int i=0;i<bValuesTotal;i++){
        if(std::find(bValuesToExclude.begin(), bValuesToExclude.end(), bValues[i]) 
            != bValuesToExclude.end()){
          bValuesMask[i] = false;
          bValuesSelected--;
        }
      }
    } else {
      // by default, all b-values will be used
      bValuesSelected = bValuesTotal;
      memset(bValuesMask,true,sizeof(bool)*bValuesTotal);
    }

    if(bValuesSelected<2){
      std::cerr << "ERROR: Less than 2 values selected, cannot do the fit!" << std::endl;
      return -1;
    }

    bValuesPtr = new float[bValuesSelected];
    imageValuesPtr = new float[bValuesSelected];
    int j = 0;
    std::cout << "Will use the following b-values: ";
    for(int i=0;i<bValuesTotal;i++){
      if(bValuesMask[i]){
        std::cout << bValues[i] << " ";
        bValuesPtr[j++] = bValues[i];
      }
    }
    std::cout << std::endl;
  } catch (itk::ExceptionObject &exc) {
    itkGenericExceptionMacro(<< exc.GetDescription() 
            << " Image " << imageName 
            << " does not contain sufficient attributes to support algorithms.");
    return EXIT_FAILURE;
  }

  MapVolumeType::Pointer slowDiffMap = MapVolumeType::New();
  slowDiffMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  slowDiffMap->Allocate();
  slowDiffMap->FillBuffer(0);
  slowDiffMap->CopyInformation(maskVolume);
  slowDiffMap->FillBuffer(0);

  MapVolumeType::Pointer fastDiffMap = MapVolumeType::New();
  fastDiffMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  fastDiffMap->Allocate();
  fastDiffMap->FillBuffer(0);
  fastDiffMap->CopyInformation(maskVolume);
  fastDiffMap->FillBuffer(0);

  MapVolumeType::Pointer fastDiffFractionMap = MapVolumeType::New();
  fastDiffFractionMap->SetRegions(maskVolume->GetLargestPossibleRegion());
  fastDiffFractionMap->Allocate();
  fastDiffFractionMap->FillBuffer(0);
  fastDiffFractionMap->CopyInformation(maskVolume);
  fastDiffFractionMap->FillBuffer(0);

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
  MapVolumeIteratorType diffIt(slowDiffMap, slowDiffMap->GetLargestPossibleRegion());
  MapVolumeIteratorType perfIt(fastDiffMap, fastDiffMap->GetLargestPossibleRegion());
  MapVolumeIteratorType perfFracIt(fastDiffFractionMap, fastDiffFractionMap->GetLargestPossibleRegion());
  MapVolumeIteratorType rsqrIt(rsqrMap, rsqrMap->GetLargestPossibleRegion());
  VectorVolumeIteratorType fittedIt(fittedVolume, fittedVolume->GetLargestPossibleRegion());

  itk::LevenbergMarquardtOptimizer::Pointer optimizer = itk::LevenbergMarquardtOptimizer::New();
  MultiExpDecayCostFunction::Pointer costFunction = MultiExpDecayCostFunction::New();
  MultiExpDecayCostFunction::ParametersType initialValue = MultiExpDecayCostFunction::ParametersType(4);
  unsigned numValues = inputVectorVolume->GetNumberOfComponentsPerPixel();

  initialValue[0] = 5000; // use b0
  initialValue[1] = 0.7; 
  initialValue[2] = 0.00025; 
  initialValue[3] = 0.002; 

  int cnt = 0;
  vvIt.GoToBegin();mvIt.GoToBegin();rsqrIt.GoToBegin();
  perfIt.GoToBegin();diffIt.GoToBegin();perfFracIt.GoToBegin();fittedIt.GoToBegin();
  for(;!diffIt.IsAtEnd();++vvIt,++mvIt,++perfIt,++diffIt,++perfFracIt,++fittedIt,++rsqrIt){
    //if(cnt>10)
    //  break;
    VectorVolumeType::PixelType vectorVoxel = vvIt.Get();
    VectorVolumeType::PixelType fittedVoxel(vectorVoxel.GetSize());
    for(int i=0;i<fittedVoxel.GetSize();i++)
     fittedVoxel[i] = 0;

    if(mvIt.Get() && vectorVoxel[0]){
      //cnt++;

      // use only those values that were requested by the user
      costFunction->SetX(bValuesPtr, bValuesSelected);
      const float* imageVector = const_cast<float*>(vectorVoxel.GetDataPointer());
      int j = 0;
      for(int i=0;i<bValuesTotal;i++){
        if(bValuesMask[i]){
          imageValuesPtr[j++] = imageVector[i];
        }
      }

      int numberOfSelectedPoints = j;
      costFunction->SetNumberOfValues(numberOfSelectedPoints);

      costFunction->SetY(imageValuesPtr,bValuesSelected);

      initialValue[0] = vectorVoxel[0];
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
          std::cerr << " Exception caught: " << e << std::endl;

      }

     itk::LevenbergMarquardtOptimizer::ParametersType finalPosition;

     finalPosition = optimizer->GetCurrentPosition();
     for(int i=0;i<fittedVoxel.GetSize();i++){
       fittedVoxel[i] = costFunction->GetFittedValue(finalPosition, bValues[i]);
       //std::cout << fittedVoxel[i] << " ";
     }
     //std::cout << std::endl;
     fittedIt.Set(fittedVoxel);

     perfFracIt.Set(finalPosition[1]);
     diffIt.Set(finalPosition[2]*1e+6);
     perfIt.Set(finalPosition[3]*1e+6);

     // initialize the rsqr map
     // see PkModeling/CLI/itkConcentrationToQuantitativeImageFilter.hxx:452
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
   }
  }


  if(slowDiffMapFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(slowDiffMap);
    writer->SetFileName(slowDiffMapFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }
  if(fastDiffMapFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(fastDiffMap);
    writer->SetFileName(fastDiffMapFileName.c_str());
    writer->SetUseCompression(1);
    writer->Update();
  }
  if(fastDiffFractionMapFileName.size()){
    MapWriterType::Pointer writer = MapWriterType::New();
    writer->SetInput(fastDiffFractionMap);
    writer->SetFileName(fastDiffFractionMapFileName.c_str());
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
