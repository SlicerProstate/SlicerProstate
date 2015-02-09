#include "itkSmoothingRecursiveGaussianImageFilter.h"
#include "itkBinaryThresholdImageFilter.h"
#include "itkImageFileWriter.h"
#include "itkImageFileReader.h"
#include "itkResampleImageFilter.h"
#include "itkNearestNeighborInterpolateImageFunction.h"

#include "SegmentationSmoothingCLP.h"

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  const unsigned int Dimension = 3;

  typedef itk::Image<unsigned char, 3> ImageType;
  typedef itk::Image<float, 3> FloatImageType;

  typedef itk::ImageFileReader<ImageType> ReaderType;
  typedef itk::SmoothingRecursiveGaussianImageFilter<ImageType,FloatImageType> SmootherType;
  typedef itk::ImageFileWriter<ImageType> WriterType;
  typedef itk::BinaryThresholdImageFilter<ImageType,ImageType> LabelThreshType;
  typedef itk::BinaryThresholdImageFilter<FloatImageType,ImageType> SmoothedThreshType;
  typedef itk::ResampleImageFilter<ImageType,ImageType> ResamplerType;
  typedef itk::NearestNeighborInterpolateImageFunction<ImageType> InterpolatorType;

  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName(inputImageName.c_str());
  reader->Update();

  ImageType::Pointer inputImage = reader->GetOutput();

  ImageType::SpacingType inputSpacing = inputImage->GetSpacing();
  ImageType::SpacingType outputSpacing, smoothSpacing;
  float minSpacing = fmin(fmin(inputSpacing[0],inputSpacing[1]),inputSpacing[2]);
  float maxSpacing = fmax(fmax(inputSpacing[0],inputSpacing[1]),inputSpacing[2]);
  outputSpacing[0] = minSpacing;
  outputSpacing[1] = minSpacing;
  outputSpacing[2] = minSpacing;
  smoothSpacing[0] = maxSpacing;
  smoothSpacing[1] = maxSpacing;
  smoothSpacing[2] = maxSpacing;

  ImageType::SizeType outputSize, inputSize;
  inputSize = inputImage->GetLargestPossibleRegion().GetSize();
  typedef ImageType::SizeType::SizeValueType SizeValueType;
  outputSize[0] = static_cast<SizeValueType>(inputSize[0]*inputSpacing[0]/outputSpacing[0] + .5);
  outputSize[1] = static_cast<SizeValueType>(inputSize[1]*inputSpacing[1]/outputSpacing[0] + .5);
  outputSize[2] = static_cast<SizeValueType>(inputSize[2]*inputSpacing[2]/outputSpacing[0] + .5);

  typedef itk::IdentityTransform<double,3> TransformType;
  TransformType::Pointer eye = TransformType::New();
  eye->SetIdentity();

  InterpolatorType::Pointer interp = InterpolatorType::New();
  ResamplerType::Pointer resampler = ResamplerType::New();
  resampler->SetOutputSpacing(outputSpacing);
  resampler->SetOutputDirection(inputImage->GetDirection());
  resampler->SetOutputOrigin(inputImage->GetOrigin());
  resampler->UseReferenceImageOff();
  resampler->SetInterpolator(interp);  
  resampler->SetSize(outputSize);
  resampler->SetTransform(eye);
  resampler->SetInput(inputImage);
  try{
    resampler->Update();
  } catch(itk::ExceptionObject &e){
    std::cout << "Resampling failed" << std::endl;
  }
  if(0){
    typedef itk::ImageFileWriter<ImageType > WriterType;
    WriterType::Pointer imageWriter = WriterType::New();
    imageWriter->SetInput(resampler->GetOutput() );
    imageWriter->SetFileName( outputImageName.c_str() );
    imageWriter->UseCompressionOn();
    imageWriter->Update();
  }

  // convert to label 1 first, then smooth, then threshold at 0.5
  LabelThreshType::Pointer labelThresh = LabelThreshType::New();
  labelThresh->SetInput(resampler->GetOutput());
  labelThresh->SetInsideValue(1);
  labelThresh->SetUpperThreshold(255);
  labelThresh->SetLowerThreshold(1);

  try{
    labelThresh->Update();
  } catch(itk::ExceptionObject &e){
    std::cout << "label threshold failed" << std::endl;
  }

  SmootherType::Pointer smoother = SmootherType::New();
  smoother->SetInput(labelThresh->GetOutput());  
  smoother->SetSigmaArray(smoothSpacing);  
  std::cout << " Sigma : " << inputSpacing <<std::endl;
  try{
    smoother->Update();
  } catch(itk::ExceptionObject &e){
    std::cout << "smoothing failed" << std::endl;
  }

  SmoothedThreshType::Pointer smoothThresh = SmoothedThreshType::New();
  smoothThresh->SetInput(smoother->GetOutput());
  smoothThresh->SetInsideValue(1);
  smoothThresh->SetUpperThreshold(255);
  smoothThresh->SetLowerThreshold(0.5);
  try{
    smoothThresh->Update();
  } catch(itk::ExceptionObject &e){
    std::cout << "smooth thresh failed" << std::endl;
  }

  {
    typedef itk::ImageFileWriter<ImageType > WriterType;
    WriterType::Pointer imageWriter = WriterType::New();
    imageWriter->SetInput(smoothThresh->GetOutput() );
    imageWriter->SetFileName( outputImageName.c_str() );
    imageWriter->UseCompressionOn();
    imageWriter->Update();
  }

  return EXIT_SUCCESS;
}
