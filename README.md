# SlicerProstate

## Introduction

SlicerProstate is an extension of 3D Slicer software (http://slicer.org) that provides a collection of modules to facilitate
* processing and management of prostate image data
* utilizing prostate images in image-guided interventions
* development of the imaging biomarkers of the prostate cancer

While the main motivation for developing the functionality contained in this extension was prostate cancer imaging applications, they can also be applied in different contexts.

See documentation at
http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/SlicerProstate.

## Functionality

Current modules include:
* [Distance Map Based Registration](http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/DistanceMapBasedRegistration): segmentation-based registration approach that can be used to support fusion of MRI-TRUS images
* [Segmentation
  Smoothing](http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/SegmentationSmoothing):
  utility to smooth segmentations done on thick-slice images
* [Quad Edge Surface
  Mesher](http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/QuadEdgeSurfaceMesher):
  utility to decimate and smooth triangular surface meshes

This extension is work in progress, and we are planning to add other modules relevant to prostate cancer imaging research .... stay tuned.


## Acknowledgments

This work supported in part the National Institutes of Health, National Cancer Institute through the following grants:
* Quantitative MRI of prostate cancer as a biomarker and guide for treatment, Quantitative Imaging Network (U01 CA151261, PI Fennessy)
* Enabling technologies for MRI-guided prostate interventions (R01 CA111288, PI Tempany)
* The National Center for Image-Guided Therapy (P41 EB015898, PI Tempany)
* Quantitative Image Informatics for Cancer Research (QIICR) (U24 CA180918, PIs Kikinis and Fedorov)

The following individuals and groups contributed directly to the development of SlicerProstate functionality:
* Andrey Fedorov, Brigham and Women's Hospital
* Andras Lasso, Queen's University

## References

If you use SlicerProstate in your work, you can acknowledge it by referencing
the following publications. You can also use those to learn more about
SlicerProstate functionality.

1. Fedorov A, Khallaghi S, Antonio Sánchez C, Lasso A, Fels S, Tuncali K, Neubauer Sugar E, Kapur T, Zhang C, Wells W, Nguyen PL, Abolmaesumi P, Tempany C. (2015) Open-source image registration for MRI–TRUS fusion-guided prostate
interventions. Int J CARS: 1–10. Available: http://link.springer.com/article/10.1007/s11548-015-1180-7. (see preprint PDF of the article [here](http://www.spl.harvard.edu/publications/item/view/2776))
2. Fedorov A, Nguyen PL, Tuncali K, Tempany C. (2015). Annotated MRI and ultrasound volume images of the prostate. Zenodo. http://doi.org/10.5281/zenodo.16396

## Contact

If you need more information, would like to contribute relevant functionality or improvement, or have suggestions for the future development please contact

Andrey Fedorov fedorov@bwh.harvard.edu
