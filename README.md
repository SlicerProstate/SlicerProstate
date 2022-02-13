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
* [DWModeling](http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/DWModeling):
  fitting of the various models to Diffusion Weighted MRI trace images


This extension is work in progress, and we are planning to add other modules relevant to prostate cancer imaging research .... stay tuned.


## Acknowledgments

This work supported in part the National Institutes of Health, National Cancer Institute through the following grants:
* Quantitative MRI of prostate cancer as a biomarker and guide for treatment, Quantitative Imaging Network (U01 CA151261, PI Fennessy)
* Enabling technologies for MRI-guided prostate interventions (R01 CA111288, PI Tempany)
* The National Center for Image-Guided Therapy (P41 EB015898, PI Tempany)
* Advancement and Validation of Prostate Diffusion and Spectroscopic MRI (R01 CA160902, PI Maier)
* Quantitative Image Informatics for Cancer Research (QIICR) (U24 CA180918, PIs Kikinis and Fedorov)

The following individuals and groups contributed directly to the development of SlicerProstate functionality:
* Andrey Fedorov, Brigham and Women's Hospital
* Andras Lasso, Queen's University
* Alireza Mehrtash, Brigham and Women's Hospital

## References

If you use SlicerProstate in your work, we would be grateful if you could acknowledge it by citing
the following publication. You can also use it to learn more about SlicerProstate functionality!

> Fedorov, A., Khallaghi, S., Sánchez, C. A., Lasso, A., Fels, S., Tuncali, K., Sugar, E. N., Kapur, T., Zhang, C., Wells, W., Nguyen, P. L., Abolmaesumi, P. & Tempany, C. Open-source image registration for MRI-TRUS fusion-guided prostate interventions. Int. J. Comput. Assist. Radiol. Surg. 10, 925–934 (2015). Available: https://pubmed.ncbi.nlm.nih.gov/25847666/

A sample dataset you can use for testing is available here. If you use this dataset, please cite it!

> Fedorov A, Nguyen PL, Tuncali K, Tempany C. (2015). Annotated MRI and ultrasound volume images of the prostate. Zenodo. http://doi.org/10.5281/zenodo.16396

## Contact

If you need more information, would like to contribute relevant functionality or improvement, or have suggestions for the future development please contact

Andrey Fedorov fedorov@bwh.harvard.edu
