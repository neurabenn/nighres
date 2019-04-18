import numpy as np
import nibabel as nb
import os
import sys
import nighresjava
from ..io import load_volume, save_volume
from ..utils import _output_dir_4saving, _fname_4saving, \
                    _check_topology_lut_dir, _check_available_memory


def conditional_shape(target_images, subjects, structures, contrasts,
                      recompute=True,
                      levelset_images=None, contrast_images=None,
                      shape_atlas_probas=None, shape_atlas_labels=None, 
                      histograms=True, intensity_atlas_hist=None,
                      intensity_atlas_mean=None, intensity_atlas_stdv=None,
                      cancel_bg=False, cancel_all=False, 
                      sum_proba=False, max_proba=False,
                      max_iterations=20, max_difference=0.01, ngb_size=4,
                      save_data=False, overwrite=False, output_dir=None,
                      file_name=None):
    """ Conditioanl Shape Parcellation

    Estimates subcortical structures based on a multi-atlas approach on shape

    Parameters
    ----------
    target_images: [niimg]
        Input images to perform the parcellation from
    subjects: int
        Number of atlas subjects
    structures: int
        Number of structures to parcellate
    contrasts: int
       Number of image intensity contrasts
    recompute: bool
        Whether to recompute shape and intensity priors from atlas images 
        (default is True)
    levelset_images: [niimg]
        Atlas shape levelsets indexed by (subjects,structures)
    contrast_images: [niimg]
        Atlas images to use in the parcellation, indexed by (subjects, contrasts)
    shape_atlas_probas: [niimg]
        Pre-computed shape atlas from the shape levelsets (replacing them)
    shape_atlas_labels: [niimg]
        Pre-computed shape atlas from the shape levelsets (replacing them)
    histograms: bool
        Whether to use complete histograms for intensity priors (default is True)
    intensity_atlas_hist: [niimg]
        Pre-computed intensity atlas from the contrast images (replacing them)
    intensity_atlas_mean: [niimg]
        Pre-computed intensity atlas from the contrast images (replacing them)
    intensity_atlas_stdv: [niimg]
        Pre-computed intensity atlas from the contrast images (replacing them)
    cancel_bg: bool
        Cancel the main background class (default is False)
    cancel_all: bool
        Cancel all main classes (default is False)
    sum_proba: bool
        Output the sum of conditional probabilities (default is False)
    max_proba: bool
        Output the max of conditional probabilities (default is False)
    max_iterations: int
        Maximum number of diffusion iterations to perform
    max_difference: float
        Maximum difference between diffusion steps
    save_data: bool
        Save output data to file (default is False)
    overwrite: bool
        Overwrite existing results (default is False)
    output_dir: str, optional
        Path to desired output directory, will be created if it doesn't exist
    file_name: str, optional
        Desired base name for output files with file extension
        (suffixes will be added)

    Returns
    ----------
    dict
        Dictionary collecting outputs under the following keys
        (suffix of output files in brackets)

        * max_spatial_proba (niimg): Maximum spatial probability map (_cspmax-sproba)
        * max_spatial_label (niimg): Maximum spatial probability labels (_cspmax-slabel)
        * max_intensity_proba (niimg): Maximum intensity probability map (_cspmax-iproba)
        * max_intensity_label (niimg): Maximum intensity probability labels (_cspmax-ilabel)
        * max_proba (niimg): Maximum probability map (_cspmax-proba)
        * max_label (niimg): Maximum probability labels (_cspmax-label)
        * cond_mean (niimg): Conditional intensity mean (_cspmax-cmean)
        * cond_stdv (niimg): Conditional intensity stdv (_cspmax-cstdv)
        * cond_hist (niimg): Conditional intensity histograms (_cspmax-chist)
        * neighbors (niimg): Local neighborhood maps (_cspmax-ngb)

    Notes
    ----------
    Original Java module by Pierre-Louis Bazin.
    """

    print('\nConditional Shape Parcellation')

    # make sure that saving related parameters are correct
    if save_data:
        output_dir = _output_dir_4saving(output_dir, target_images[0])

        spatial_proba_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                  rootfile=target_images[0],
                                  suffix='cspmax-sproba', ))

        spatial_label_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                   rootfile=target_images[0],
                                   suffix='cspmax-slabel'))
        intensity_proba_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                  rootfile=target_images[0],
                                  suffix='cspmax-iproba', ))

        intensity_label_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                   rootfile=target_images[0],
                                   suffix='cspmax-ilabel'))
        proba_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                  rootfile=target_images[0],
                                  suffix='cspmax-proba', ))

        label_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                   rootfile=target_images[0],
                                   suffix='cspmax-label'))

        condmean_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                  rootfile=target_images[0],
                                  suffix='cspmax-cmean', ))

        condstdv_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                   rootfile=target_images[0],
                                   suffix='cspmax-cstdv'))
        
        condhist_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                   rootfile=target_images[0],
                                   suffix='cspmax-chist'))
        
        neighbor_file = os.path.join(output_dir, 
                        _fname_4saving(file_name=file_name,
                                   rootfile=target_images[0],
                                   suffix='cspmax-ngb'))
        if overwrite is False \
            and os.path.isfile(spatial_proba_file) \
            and os.path.isfile(spatial_label_file) \
            and os.path.isfile(intensity_proba_file) \
            and os.path.isfile(intensity_label_file) \
            and os.path.isfile(proba_file) \
            and os.path.isfile(label_file) \
            and os.path.isfile(neighbor_file) \
            and ( (histograms and os.path.isfile(condhist_file)) \
            or (os.path.isfile(condmean_file) \
            and os.path.isfile(condstdv_file)) ):
            
            print("skip computation (use existing results)")
            output = {'max_spatial_proba': load_volume(spatial_proba_file), 
                      'max_spatial_label': load_volume(spatial_label_file),
                      'max_intensity_proba': load_volume(intensity_proba_file), 
                      'max_intensity_label': load_volume(intensity_label_file),
                      'max_proba': load_volume(proba_file), 
                      'max_label': load_volume(label_file),
                      'neighbors': load_volume(neighbor_file)}
            if histograms:
                output.update(cond_hist=load_volume(condhist_file))
            else:
                output.update(cond_mean=load_volume(condmean_file)) 
                output.update(cond_stdv=load_volume(condstdv_file))
            return output


    # start virtual machine, if not already running
    try:
        mem = _check_available_memory()
        nighresjava.initVM(initialheap=mem['init'], maxheap=mem['max'])
    except ValueError:
        pass
    # create instance
    cspmax = nighresjava.ConditionalShapeSegmentation()

    # set parameters
    cspmax.setNumberOfSubjectsObjectsAndContrasts(subjects,structures,contrasts)
    cspmax.setOptions(True, cancel_bg, cancel_all, sum_proba, max_proba)
    cspmax.setDiffusionParameters(max_iterations, max_difference)
    
    # load target image for parameters
    print("load: "+str(target_images[0]))
    img = load_volume(target_images[0])
    data = img.get_data()
    affine = img.get_affine()
    header = img.get_header()
    resolution = [x.item() for x in header.get_zooms()]
    dimensions = data.shape

    cspmax.setDimensions(dimensions[0], dimensions[1], dimensions[2])
    cspmax.setResolutions(resolution[0], resolution[1], resolution[2])

    # target image 1
    cspmax.setTargetImageAt(0, nighresjava.JArray('float')(
                                            (data.flatten('F')).astype(float)))
    
    # if further contrast are specified, input them
    for contrast in range(1,contrasts):    
        print("load: "+str(target_images[contrast]))
        data = load_volume(target_images[contrast]).get_data()
        cspmax.setTargetImageAt(contrast, nighresjava.JArray('float')(
                                            (data.flatten('F')).astype(float)))

    # load the shape and intensity atlases, if existing
    if recompute:
        # load the atlas structures and contrasts, if needed
        for sub in range(subjects):
            for struct in range(structures):
                print("load: "+str(levelset_images[sub][struct]))
                data = load_volume(levelset_images[sub][struct]).get_data()
                cspmax.setLevelsetImageAt(sub, struct, nighresjava.JArray('float')(
                                                    (data.flatten('F')).astype(float)))
                    
            for contrast in range(contrasts):
                print("load: "+str(contrast_images[sub][contrast]))
                data = load_volume(contrast_images[sub][contrast]).get_data()
                cspmax.setContrastImageAt(sub, contrast, nighresjava.JArray('float')(
                                                    (data.flatten('F')).astype(float)))
    else:         
        if histograms:
            print("load: "+str(os.path.join(output_dir,intensity_atlas_hist)))
            data = load_volume(os.path.join(output_dir,intensity_atlas_hist)).get_data()
            cspmax.setConditionalHistogram(nighresjava.JArray('float')(
                                                (data.flatten('F').astype(float))))
        else:
            print("load: "+str(os.path.join(output_dir,intensity_atlas_mean)))
            mean = load_volume(os.path.join(output_dir,intensity_atlas_mean)).get_data()
            print("load: "+str(os.path.join(output_dir,intensity_atlas_stdv)))
            stdv = load_volume(os.path.join(output_dir,intensity_atlas_stdv)).get_data()
            cspmax.setConditionalMeanAndStdv(nighresjava.JArray('float')(
                                                (mean.flatten('F')).astype(float)),
                                            nighresjava.JArray('float')(
                                                (stdv.flatten('F')).astype(float)))

        print("load: "+str(os.path.join(output_dir,shape_atlas_probas)))
        pdata = load_volume(os.path.join(output_dir,shape_atlas_probas)).get_data()
        print("load: "+str(os.path.join(output_dir,shape_atlas_labels)))
        ldata = load_volume(os.path.join(output_dir,shape_atlas_labels)).get_data()
        cspmax.setShapeAtlasProbasAndLabels(nighresjava.JArray('float')(
                                    (pdata.flatten('F')).astype(float)),
                                    nighresjava.JArray('int')(
                                    (ldata.flatten('F')).astype(int).tolist()))

    # execute
    try:
        #cspmax.execute()
        if recompute: cspmax.computeAtlasPriors()
        cspmax.estimateTarget()
        cspmax.strictSimilarityDiffusion(ngb_size)
        #cspmax.similarityDiffusion(6)
        #cspmax.dissimilarityDiffusion(6)
        #cspmax.transitionDiffusion()
        if not recompute: 
            cspmax.collapseConditionalMaps()
            cspmax.optimalVolumeThreshold(1.0, 0.05, True)

    except:
        # if the Java module fails, reraise the error it throws
        print("\n The underlying Java code did not execute cleanly: ")
        print(sys.exc_info()[0])
        raise
        return

    # reshape output to what nibabel likes
    dimensions = (dimensions[0],dimensions[1],dimensions[2],cspmax.getBestDimension())
    dims3D = (dimensions[0],dimensions[1],dimensions[2])
    dims_ngb = (dimensions[0],dimensions[1],dimensions[2],ngb_size)
    
    intens_dims = (structures+1,structures+1,contrasts)

    intens_hist_dims = ((structures+1)*(structures+1),cspmax.getNumberOfBins()+4,contrasts)

    if recompute:
        spatial_proba_data = np.reshape(np.array(cspmax.getBestSpatialProbabilityMaps(dimensions[3]),
                                       dtype=np.float32), dimensions, 'F')
    
        spatial_label_data = np.reshape(np.array(cspmax.getBestSpatialProbabilityLabels(dimensions[3]),
                                        dtype=np.int32), dimensions, 'F')    

        intensity_proba_data = np.reshape(np.array(cspmax.getBestIntensityProbabilityMaps(dimensions[3]),
                                       dtype=np.float32), dimensions, 'F')
    
        intensity_label_data = np.reshape(np.array(cspmax.getBestIntensityProbabilityLabels(dimensions[3]),
                                        dtype=np.int32), dimensions, 'F')
    
        proba_data = np.reshape(np.array(cspmax.getBestProbabilityMaps(dimensions[3]),
                                       dtype=np.float32), dimensions, 'F')
    
        label_data = np.reshape(np.array(cspmax.getBestProbabilityLabels(dimensions[3]),
                                        dtype=np.int32), dimensions, 'F')
    else:
        spatial_proba_data = np.reshape(np.array(cspmax.getBestSpatialProbabilityMaps(1),
                                       dtype=np.float32), dims3D, 'F')
    
        spatial_label_data = np.reshape(np.array(cspmax.getBestSpatialProbabilityLabels(1),
                                        dtype=np.int32), dims3D, 'F')    

        intensity_proba_data = np.reshape(np.array(cspmax.getBestIntensityProbabilityMaps(1),
                                       dtype=np.float32), dims3D, 'F')
    
        intensity_label_data = np.reshape(np.array(cspmax.getBestIntensityProbabilityLabels(1),
                                        dtype=np.int32), dims3D, 'F')
    
        proba_data = np.reshape(np.array(cspmax.getCertaintyProbability(),
                                       dtype=np.float32), dims3D, 'F')
    
        label_data = np.reshape(np.array(cspmax.getBestProbabilityLabels(1),
                                        dtype=np.int32), dims3D, 'F')

    neighbor_data = np.reshape(np.array(cspmax.getNeighborhoodMaps(ngb_size),
                                        dtype=np.float32), dims_ngb, 'F')

    if histograms:
        intens_hist_data = np.reshape(np.array(cspmax.getConditionalHistogram(),
                                       dtype=np.float32), intens_hist_dims, 'F')
    else:
        intens_mean_data = np.reshape(np.array(cspmax.getConditionalMean(),
                                       dtype=np.float32), intens_dims, 'F')
    
        intens_stdv_data = np.reshape(np.array(cspmax.getConditionalStdv(),
                                        dtype=np.float32), intens_dims, 'F')

    # adapt header max for each image so that correct max is displayed
    # and create nifiti objects
    header['cal_max'] = np.nanmax(spatial_proba_data)
    spatial_proba = nb.Nifti1Image(spatial_proba_data, affine, header)

    header['cal_max'] = np.nanmax(spatial_label_data)
    spatial_label = nb.Nifti1Image(spatial_label_data, affine, header)

    header['cal_max'] = np.nanmax(intensity_proba_data)
    intensity_proba = nb.Nifti1Image(intensity_proba_data, affine, header)

    header['cal_max'] = np.nanmax(intensity_label_data)
    intensity_label = nb.Nifti1Image(intensity_label_data, affine, header)

    header['cal_max'] = np.nanmax(proba_data)
    proba = nb.Nifti1Image(proba_data, affine, header)

    header['cal_max'] = np.nanmax(label_data)
    label = nb.Nifti1Image(label_data, affine, header)

    header['cal_min'] = np.nanmin(neighbor_data)
    header['cal_max'] = np.nanmax(neighbor_data)
    neighbors = nb.Nifti1Image(neighbor_data, affine, header)

    if histograms:
        chist = nb.Nifti1Image(intens_hist_data, None, None)
    else:
        cmean = nb.Nifti1Image(intens_mean_data, None, None)
        cstdv = nb.Nifti1Image(intens_stdv_data, None, None)

    if save_data:
        save_volume(spatial_proba_file, spatial_proba)
        save_volume(spatial_label_file, spatial_label)
        save_volume(intensity_proba_file, intensity_proba)
        save_volume(intensity_label_file, intensity_label)
        save_volume(proba_file, proba)
        save_volume(label_file, label)
        save_volume(neighbor_file, neighbors)
        if histograms:
            save_volume(condhist_file, chist)
        else:
            save_volume(condmean_file, cmean)
            save_volume(condstdv_file, cstdv)

    output= {'max_spatial_proba': spatial_proba, 'max_spatial_label': spatial_label, 
            'max_intensity_proba': intensity_proba, 'max_intensity_label': intensity_label, 
            'max_proba': proba, 'max_label': label, 'neighbors': neighbors}
    if histograms:
        output.update(cond_hist=chist)
    else:
        output.update(cond_mean=cmean) 
        output.update(cond_stdv=cstdv)
    return output
