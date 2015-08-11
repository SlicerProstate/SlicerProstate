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
      if (tag.find("B-value") != std::string::npos)
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

class DecayCostFunction: public itk::MultipleValuedCostFunction
{
public:
  typedef DecayCostFunction                    Self;
  typedef itk::MultipleValuedCostFunction   Superclass;
  typedef itk::SmartPointer<Self>           Pointer;
  typedef itk::SmartPointer<const Self>     ConstPointer;
  itkNewMacro( Self );

  typedef Superclass::ParametersType              ParametersType;
  typedef Superclass::DerivativeType              DerivativeType;
  typedef Superclass::MeasureType                 MeasureType, ArrayType;
  typedef Superclass::ParametersValueType         ValueType;

  enum Model {
    MonoExponential = 0,
    BiExponential = 1,
    Kurtosis = 2,
    StretchedExponential = 3,
    Gamma = 4
  };

  enum { SpaceDimension =  3 };

  DecayCostFunction()
  {
    modelType = BiExponential;
  }

  void SetModelType(Model mt){
    modelType = mt;
    switch(modelType){
    case BiExponential:
      // initialize initial parameters
      initialValue = ParametersType(4);
      initialValue[0] = 0; // set to b0!
      initialValue[1] = 0.7;
      initialValue[2] = 0.00025;
      initialValue[3] = 0.002;

      // initialize parameter meaning (store this in NRRD? save units?)
      parametersMeaning.clear();
      parametersMeaning.push_back("Scale");
      parametersMeaning.push_back("Fast diffusion fraction");
      parametersMeaning.push_back("Slow diffusion coefficient");
      parametersMeaning.push_back("Fast diffusion coefficient");

      break;
    case Kurtosis:
      // initialize initial parameters
      initialValue = ParametersType(3);
      initialValue[0] = 0; // set to b0!
      initialValue[1] = 1;
      initialValue[2] = 0.0015;

      // initialize parameter meaning (store this in NRRD? save units?)
      parametersMeaning.clear();
      parametersMeaning.push_back("Scale");
      parametersMeaning.push_back("Kurtosis");
      parametersMeaning.push_back("Kurtosis diffusion");

      break;
    case MonoExponential:
      initialValue = ParametersType(2);
      initialValue[0] = 0;
      initialValue[1] = 0.0015;

      // initialize parameter meaning (store this in NRRD? save units?)
      parametersMeaning.clear();
      parametersMeaning.push_back("Scale");
      parametersMeaning.push_back("ADC");

      break;
    case StretchedExponential:
      initialValue = ParametersType(3);
      initialValue[0] = 0;
      initialValue[1] = 0.0017;
      initialValue[2] = 0.7;

      parametersMeaning.clear();
      // See Bennett et al. 2003
      // Bennett KM, Schmainda KM, Bennett RT, Rowe DB, Lu H, Hyde JS.
      // Characterization of continuously distributed cortical water diffusion
      // rates with a stretched-exponential model.
      // Magn Reson Med. 2003;50: 727–734. doi:10.1002/mrm.10581
      parametersMeaning.push_back("Scale");
      // the quantity derived from fitting the stretched-exponential
      // function to the data
      parametersMeaning.push_back("Distributed Diffusion Coefficient (DDC)");
      // Stretching parameter between 0 and 1 characterizing deviation of the
      // signal attennuation from the monoexponential behavior
      parametersMeaning.push_back("Alpha");

      break;

    case Gamma:
      initialValue = ParametersType(3);
      initialValue[0] = 0;
      initialValue[1] = 1.5;
      initialValue[2] = 0.002;

      parametersMeaning.clear();
      // See Oshio et al. 2014
      // Oshio K, Shinmoto H, Mulkern RV. Interpretation of diffusion MR
      // imaging data using a gamma distribution model.
      // Magn Reson Med Sci. 2014;13: 191–195. doi:10.2463/mrms.2014-0016
      parametersMeaning.push_back("Scale");
      parametersMeaning.push_back("k parameter of the gamma distribution");
      parametersMeaning.push_back("theta parameter of the gamma distribution");

      break;

    default:
      abort(); // not implemented!
    }
  }

 ParametersType GetInitialValue(){
   return initialValue;
 }

  void SetInitialValues(ParametersType initialParameters){
    // TODO: add model-specific checks
    if(initialParameters.size() != initialValue.size())
      return;
    for(int i=0;i<initialValue.size();i++)
      initialValue[i] = initialParameters[i];
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

    switch(modelType){
    case BiExponential:{
      float scale = parameters[0],
          fraction = parameters[1],
          slowDiff = parameters[2],
          fastDiff = parameters[3];

      for(int i=0;i<measure.size();i++)
        {
        measure[i] =
          scale*((1-fraction)*exp(-1.*X[i]*slowDiff)+fraction*exp(-1.*X[i]*fastDiff));
        }
      break;
    }
    case Kurtosis:{
      float scale = parameters[0],
          kurtosis = parameters[1],
          kurtosisDiff = parameters[2]; //TK

      for(int i=0;i<measure.size();i++)
        {
        measure[i] =
          scale*(exp(-1.*X[i]*kurtosisDiff+((X[i]*X[i])*(kurtosisDiff*kurtosisDiff)*kurtosis/6))); //TK
        }
      break;
      }
    case MonoExponential:{
      float scale = parameters[0],
          adc = parameters[1];

      for(int i=0;i<measure.size();i++)
        {
        measure[i] =
          scale*exp(-1.*X[i]*adc);
        }
      break;
    }
    case StretchedExponential:{
      float scale = parameters[0],
        DDC = parameters[1],
        alpha = parameters[2];

      for(int i=0;i<measure.size();i++){
        measure[i] = scale*(exp(-(pow(double(X[i]*DDC), double(alpha)))));
      }
      break;
    }
    case Gamma:
    {
      float scale = parameters[0],
        k = parameters[1], theta = parameters[2];

      for(int i=0;i<measure.size();i++){
        measure[i] = scale/(pow(double(1+X[i]*theta), double(k)));
      }
      break;
    }
    default:
      abort();
    }

    return measure;
  }

  float GetFittedValue(const ParametersType & parameters, float x) const
  {
    float measure;
    switch(modelType){
    case BiExponential:{
      float scale = parameters[0],
          fraction = parameters[1],
          slowDiff = parameters[2],
          fastDiff = parameters[3];

      measure =
        scale*((1-fraction)*exp(-1.*x*slowDiff)+fraction*exp(-1.*x*fastDiff));
      break;
    }
    case Kurtosis:{
      float scale = parameters[0],
          kurtosis = parameters[1],
          kurtosisDiff = parameters[2];
      measure =
        scale*(exp(-1.*x*kurtosisDiff+((x*x)*(kurtosisDiff*kurtosisDiff)*kurtosis/6)));
      break;
    }
    case MonoExponential:{
      float scale = parameters[0],
          adc = parameters[1];
      measure =
          scale*exp(-1.*x*adc);
      break;
    }
    case StretchedExponential:{
      float scale = parameters[0],
        DDC = parameters[1],
        alpha = parameters[2];
        measure = scale*(exp(-(pow(double(x*DDC), double(alpha)))));
      break;
    }
    case Gamma:
    {
      float scale = parameters[0],
        k = parameters[1], theta = parameters[2];
      measure = scale/(pow(double(1+x*theta), double(k)));
      break;
    }
    default:
      abort();
    }

    return measure;
  }

  MeasureType GetValue( const ParametersType & parameters) const
  {
    MeasureType measure(RangeDimension);

    switch(modelType){
    case BiExponential:{
      float scale = parameters[0],
          fraction = parameters[1],
          slowDiff = parameters[2],
          fastDiff = parameters[3];

      for(int i=0;i<measure.size();i++)
        {
        measure[i] =
          Y[i]-scale*((1-fraction)*exp(-1.*X[i]*slowDiff)+fraction*exp(-1.*X[i]*fastDiff));
        }
      break;
    }
    case Kurtosis:{
      float scale = parameters[0],
          kurtosis = parameters[1],
          kurtosisDiff = parameters[2];

      for(int i=0;i<measure.size();i++)
        {
        measure[i] =
          Y[i]-scale*(exp(-1.*X[i]*kurtosisDiff+((X[i]*X[i])*(kurtosisDiff*kurtosisDiff)*kurtosis/6)));
        }
      break;
    }
    case MonoExponential:{
      float scale = parameters[0],
          adc = parameters[1];

      for(int i=0;i<measure.size();i++)
        {
        measure[i] =
          Y[i]-scale*exp(-1.*X[i]*adc);
        }
      break;
    }
    case StretchedExponential:{
      float scale = parameters[0],
        DDC = parameters[1],
        alpha = parameters[2];

      for(int i=0;i<measure.size();i++){
        measure[i] = Y[i]-scale*(exp(-(pow(double(X[i]*DDC), double(alpha)))));
      }
      break;
    }
    case Gamma:
    {
      float scale = parameters[0],
        k = parameters[1], theta = parameters[2];

      for(int i=0;i<measure.size();i++){
        measure[i] = Y[i]-scale/(pow(double(1+X[i]*theta), double(k)));
      }
      break;
    }
    default:
      abort(); // not implemented
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
    switch(modelType){
    case MonoExponential: return 2;
    case BiExponential: return 4;
    case Kurtosis: return 3;
    case StretchedExponential: return 3;
    case Gamma: return 3;
    default: return 0; // should never get here
    }
  }

  void SetNumberOfValues(unsigned int nValues)
    {
    RangeDimension = nValues;
    }

  unsigned int GetNumberOfValues(void) const
  {
    return RangeDimension;
  }

  Model GetModelType() const {
    return modelType;
  }

protected:
  virtual ~DecayCostFunction(){}
private:

  ArrayType X, Y;

  unsigned int RangeDimension;
  Model modelType;
  ParametersType initialValue;
  std::vector<std::string> parametersMeaning;
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

typedef itk::ImageRegionConstIterator<VectorVolumeType> InputVectorVolumeIteratorType;
typedef itk::ImageRegionIterator<VectorVolumeType> OutputVectorVolumeIteratorType;
typedef itk::ImageRegionConstIterator<MaskVolumeType> MaskVolumeIteratorType;
typedef itk::ImageRegionIterator<MapVolumeType> MapVolumeIteratorType;

void SaveMap(MapVolumeType::Pointer map, std::string fileName){
  MapWriterType::Pointer writer = MapWriterType::New();
  writer->SetInput(map);
  writer->SetFileName(fileName.c_str());
  writer->SetUseCompression(1);
  writer->Update();
}

// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
int main( int argc, char * argv[])
{
  PARSE_ARGS;

  if((bValuesToInclude.size()>0) && (bValuesToExclude.size()>0)){
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

  // allocate output maps
  DecayCostFunction::Model modelType;
  std::vector<MapVolumeType::Pointer> parameterMapVector;
  std::vector<MapVolumeIteratorType> parameterMapItVector;

  if(modelName == "BiExponential")
    modelType = DecayCostFunction::BiExponential;
  else if(modelName == "MonoExponential")
    modelType = DecayCostFunction::MonoExponential;
  else if(modelName == "Kurtosis")
    modelType = DecayCostFunction::Kurtosis;
  else if(modelName == "StretchedExponential")
    modelType = DecayCostFunction::StretchedExponential;
  else if(modelName == "Gamma")
    modelType = DecayCostFunction::Gamma;
  else {
    std::cerr << "ERROR: Unknown model type specified!" << std::endl;
    return -1;
  }

  DecayCostFunction::Pointer costFunction = DecayCostFunction::New();
  costFunction->SetModelType(modelType);

  // set initial parameters model-dependent
  DecayCostFunction::ParametersType initialValue = costFunction->GetInitialValue();
  if(modelName == "BiExponential"){
    initialValue[0] = biExpInitParameters[0];
    initialValue[1] = biExpInitParameters[1];
    initialValue[2] = biExpInitParameters[2];
    initialValue[3] = biExpInitParameters[3];
  } else if(modelName == "MonoExponential") {
    initialValue[0] = monoExpInitParameters[0];
    initialValue[1] = monoExpInitParameters[1];
  } else if(modelName == "Kurtosis") {
    initialValue[0] = kurtosisInitParameters[0];
    initialValue[1] = kurtosisInitParameters[1];
    initialValue[2] = kurtosisInitParameters[2];
  } else if(modelName == "StretchedExponential") {
    initialValue[0] = stretchedExpInitParameters[0];
    initialValue[1] = stretchedExpInitParameters[1];
    initialValue[2] = stretchedExpInitParameters[2];
  } else if(modelName == "Gamma") {
    initialValue[0] = gammaInitParameters[0];
    initialValue[1] = gammaInitParameters[1];
    initialValue[2] = gammaInitParameters[2];
  }

  costFunction->SetInitialValues(initialValue);

  unsigned numberOfMaps;
  if(modelName == "Gamma") {
    // include computed mode map as output
    numberOfMaps = costFunction->GetNumberOfParameters()+1;
  } else {
    numberOfMaps = costFunction->GetNumberOfParameters();
  }
  parameterMapVector.resize(numberOfMaps);

  for(int i=0;i<numberOfMaps;i++){
    parameterMapVector[i] = MapVolumeType::New();
    parameterMapVector[i]->SetRegions(maskVolume->GetLargestPossibleRegion());
    parameterMapVector[i]->Allocate();
    parameterMapVector[i]->FillBuffer(0);
    // note mask is initialized even if not passed by the user
    parameterMapVector[i]->CopyInformation(maskVolume);
    parameterMapVector[i]->FillBuffer(0);

    parameterMapItVector.push_back(
          MapVolumeIteratorType(parameterMapVector[i],parameterMapVector[i]->GetLargestPossibleRegion()));
    parameterMapItVector[i].GoToBegin();
  }

  // R^2 and fitted values volumes are calculated independently of the model
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

  InputVectorVolumeIteratorType vvIt(inputVectorVolume, inputVectorVolume->GetLargestPossibleRegion());
  OutputVectorVolumeIteratorType fittedIt(fittedVolume, fittedVolume->GetLargestPossibleRegion());

  MaskVolumeIteratorType mvIt(maskVolume, maskVolume->GetLargestPossibleRegion());
  MapVolumeIteratorType rsqrIt(rsqrMap, rsqrMap->GetLargestPossibleRegion());

  itk::LevenbergMarquardtOptimizer::Pointer optimizer = itk::LevenbergMarquardtOptimizer::New();

  int cnt = 0;

  for(vvIt.GoToBegin();!vvIt.IsAtEnd();++vvIt){
    //if(cnt>10)
    //  break;
    VectorVolumeType::IndexType index = vvIt.GetIndex();
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

      DecayCostFunction::ParametersType initialValue = costFunction->GetInitialValue();
      initialValue[0] = vectorVoxel[0];
      DecayCostFunction::MeasureType temp = costFunction->GetValue(initialValue);
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
        //std::cerr << "Final position: " << finalPosition << std::endl;
        //std::cout << fittedVoxel[i] << " ";
      }

      //std::cout << std::endl;
      fittedIt.Set(fittedVoxel);
      //std::cout << "Fitted voxel: " << fittedVoxel << " params: " << finalPosition << std::endl;
      switch(modelType){
        case DecayCostFunction::BiExponential:{
          parameterMapItVector[0].Set(finalPosition[0]);
          parameterMapItVector[1].Set(finalPosition[1]);
          parameterMapItVector[2].Set(finalPosition[2]*1e+6);
          parameterMapItVector[3].Set(finalPosition[3]*1e+6);
          break;
        }
        case DecayCostFunction::Kurtosis:{
          parameterMapItVector[0].Set(finalPosition[0]);
          parameterMapItVector[1].Set(finalPosition[1]);
          parameterMapItVector[2].Set(finalPosition[2]*1e+6);
          break;
        }
        case DecayCostFunction::MonoExponential:{
          parameterMapItVector[0].Set(finalPosition[0]);
          parameterMapItVector[1].Set(finalPosition[1]*1e+6);
          break;
        }
        case DecayCostFunction::StretchedExponential:{
          parameterMapItVector[0].Set(finalPosition[0]);
          parameterMapItVector[1].Set(finalPosition[1]*1e+6); // DDC
          parameterMapItVector[2].Set(finalPosition[2]); // alpha
          break;
        }
        case DecayCostFunction::Gamma:{
          parameterMapItVector[0].Set(finalPosition[0]);
          parameterMapItVector[1].Set(finalPosition[1]); // k
          parameterMapItVector[2].Set(finalPosition[2]*1e+6); // theta
          parameterMapItVector[3].Set((finalPosition[1]-1)*finalPosition[2]); // mode
          break;
        }

      default: abort();
      }

      // initialize the rsqr map
      // see PkModeling/CLI/itkConcentrationToQuantitativeImageFilter.hxx:452
      {
        double rms = optimizer->GetOptimizer()->get_end_error();
        double SSerr = rms*rms*bValuesSelected;
        double sumSquared = 0.0;
        double sum = 0.0;
        double rSquared = 0.0;

        for (unsigned int i=0; i < bValuesSelected; ++i){
          sum += imageValuesPtr[i];
          sumSquared += (imageValuesPtr[i]*imageValuesPtr[i]);
        }
        double SStot = sumSquared - sum*sum/(double)bValuesSelected;
        rSquared = 1.0 - (SSerr / SStot);
        rsqrIt.Set(rSquared);
      }
    }

    for(int i=0;i<costFunction->GetNumberOfParameters();i++){
      ++parameterMapItVector[i];
    }
    ++rsqrIt;++mvIt;++fittedIt;
  }

  switch(modelType){
    case DecayCostFunction::BiExponential:{
      if(fastDiffFractionMapFileName.size())
        SaveMap(parameterMapVector[1], fastDiffFractionMapFileName);
      if(slowDiffMapFileName.size())
        SaveMap(parameterMapVector[2], slowDiffMapFileName);
      if(fastDiffMapFileName.size())
        SaveMap(parameterMapVector[3], fastDiffMapFileName);
      break;
    }
    case DecayCostFunction::Kurtosis:{
      if(kurtosisMapFileName.size())
        SaveMap(parameterMapVector[1], kurtosisMapFileName);
      if(kurtosisDiffMapFileName.size())
        SaveMap(parameterMapVector[2], kurtosisDiffMapFileName);
      break;
    }
    case DecayCostFunction::MonoExponential:{
      if(adcMapFileName.size())
        SaveMap(parameterMapVector[1], adcMapFileName);
      break;
    }
    case DecayCostFunction::StretchedExponential:{
      if(DDCMapFileName.size())
        SaveMap(parameterMapVector[1], DDCMapFileName);
      if(alphaMapFileName.size())
        SaveMap(parameterMapVector[2], alphaMapFileName);
      break;
    }
    case DecayCostFunction::Gamma:{
      if(thetaMapFileName.size())
        SaveMap(parameterMapVector[1], kMapFileName);
      if(kMapFileName.size())
        SaveMap(parameterMapVector[2], thetaMapFileName);
      if(modeMapFileName.size())
        SaveMap(parameterMapVector[3], modeMapFileName);
      break;
    }

    default:abort();
  }

  if(rsqrVolumeFileName.size())
    SaveMap(rsqrMap, rsqrVolumeFileName);

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
