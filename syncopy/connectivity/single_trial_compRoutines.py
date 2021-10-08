# -*- coding: utf-8 -*-
#
# computeFunctions and -Routines to calculate
# single trial measures needed for the averaged
# measures like cross spectral densities
#

# Builtin/3rd party package imports
import numpy as np

# syncopy imports
from syncopy.specest.mtmfft import mtmfft
from syncopy.specest.const_def import spectralDTypes
from syncopy.shared.errors import SPYWarning
from syncopy.datatype import padding
from syncopy.shared.tools import best_match
from syncopy.shared.computational_routine import ComputationalRoutine
from syncopy.shared.kwarg_decorators import unwrap_io


def cross_spectra_cF(trl_dat,
                     samplerate=1,
                     foi=None,
                     padding_opt={},
                     taper="hann",
                     taperopt={},
                     polyremoval=False,
                     timeAxis=0,
                     noCompute=False):

    """
    Single trial Fourier cross spectra estimates between all channels
    of the input data. First all the individual Fourier transforms
    are calculated via a (multi-)tapered FFT, then the pairwise
    cross-spectra are computed. 

    Averaging over tapers is done implicitly
    for multi-taper analysis with `taper="dpss"`.

    Output consists of all (nChannels x nChannels+1)/2 different estimates
    aranged in a symmetric fashion (CS_ij == CS_ji). The elements on the
    main diagonal (CS_ii) are the auto-spectra.

    This is NOT the same as what is commonly referred to as 
    "cross spectral density" as there is no (time) averaging!!
    Multi-tapering alone usually is not sufficient to get enough
    statitstical power for a robust csd estimate.

    Parameters
    ----------
    trl_dat : (K, N) :class:`numpy.ndarray`
        Uniformly sampled multi-channel time-series data
        The 1st dimension is interpreted as the time axis,
        columns represent individual channels.
        Dimensions can be transposed to (N, K) with the `timeAxis` parameter.
    samplerate : float
        Samplerate in Hz
    foi : 1D :class:`numpy.ndarray`
        Frequencies of interest  (Hz) for output. If desired frequencies
        cannot be matched exactly the closest possible frequencies (respecting 
        data length and padding) are used.
    padding_opt : dict
        Parameters to be used for padding. See :func:`syncopy.padding` for 
        more details.
    taper : str or None
        Taper function to use, one of scipy.signal.windows
        Set to `None` for no tapering.
    taperopt : dict
        Additional keyword arguments passed to the `taper` function. 
        For multi-tapering with `taper='dpss'` set the keys 
        `'Kmax'` and `'NW'`.
        For further details, please refer to the 
        `SciPy docs <https://docs.scipy.org/doc/scipy/reference/signal.windows.html>`_
    polyremoval : int or None
        **FIXME: Not implemented yet**
        Order of polynomial used for de-trending data in the time domain prior 
        to spectral analysis. A value of 0 corresponds to subtracting the mean 
        ("de-meaning"), ``polyremoval = 1`` removes linear trends (subtracting the 
        least squares fit of a linear polynomial), ``polyremoval = N`` for `N > 1` 
        subtracts a polynomial of order `N` (``N = 2`` quadratic, ``N = 3`` cubic 
        etc.). If `polyremoval` is `None`, no de-trending is performed. 
    timeAxis : int
        Index of running time axis in `trl_dat` (0 or 1)
    noCompute : bool
        Preprocessing flag. If `True`, do not perform actual calculation but
        instead return expected shape and :class:`numpy.dtype` of output
        array.


    Returns
    -------    
    CS_ij : (1, nFreq, N, N) :class:`numpy.ndarray`
        Cross spectra for all channel combinations i,j.
        `N` corresponds to number of input channels.

    freqs : (M,) :class:`numpy.ndarray`
        The Fourier frequencies

    Notes
    -----
    This method is intended to be used as 
    :meth:`~syncopy.shared.computational_routine.ComputationalRoutine.computeFunction`
    inside a :class:`~syncopy.shared.computational_routine.ComputationalRoutine`. 
    Thus, input parameters are presumed to be forwarded from a parent metafunction. 
    Consequently, this function does **not** perform any error checking and operates 
    under the assumption that all inputs have been externally validated and cross-checked. 

    See also
    --------
    mtmfft : :func:`~syncopy.specest.mtmfft.mtmfft`
             (Multi-)tapered Fourier analysis

    """
    
    # Re-arrange array if necessary and get dimensional information
    if timeAxis != 0:
        dat = trl_dat.T       # does not copy but creates view of `trl_dat`
    else:
        dat = trl_dat

    # Symmetric Padding (updates no. of samples)
    if padding_opt:
        dat = padding(dat, **padding_opt)
        
    nChannels = dat.shape[1]

    # specs has shape (nTapers x nFreq x nChannels)    
    specs, freqs = mtmfft(trl_dat, samplerate, taper, taperopt)
    if foi is not None:
        _, freq_idx = best_match(freqs, foi, squash_duplicates=True)
        nFreq = freq_idx.size        
    else:
        freq_idx = slice(None)
        nFreq = freqs.size
        
    # we always average over tapers here
    # use dummy time-axis
    outShape = (1, nFreq, nChannels, nChannels)
    
    # For initialization of computational routine,
    # just return output shape and dtype
    # cross spectra are complex!
    if noCompute:
        return outShape, spectralDTypes["fourier"]

    # outer product along channel axes
    # has shape (nTapers x nFreq x nChannels x nChannels)        
    CS_ij = specs[:, :, np.newaxis, :] * specs[:, :, :, np.newaxis].conj()
    
    # average tapers and transpose:
    # now has shape (nChannels x nChannels x nFreq)        
    CS_ij = CS_ij.mean(axis=0).T

    # where does freqs go/come from?!
    return freqs[freq_idx], CS_ij[np.newaxis, ..., freq_idx]


def covariance_cF(trl_dat):

    """
    Single trial covariance estimates between all channels
    of the input data. Output consists of all (nChannels x nChannels+1)/2 
    different estimates aranged in a symmetric fashion 
    (COV_ij == COV_ji). The elements on the
    main diagonal (CS_ii) are the channel variances.

    Parameters
    ----------
    trl_dat : (K, N) :class:`numpy.ndarray`
        Uniformly sampled multi-channel time-series data
        The 1st dimension is interpreted as the time axis,
        columns represent individual channels.

    Returns
    -------    
    COV_ij : (N, N, M) :class:`numpy.ndarray`
        Covariances for all channel combinations i,j.

    See also
    --------

    
    mtmfft : :func:`~syncopy.specest.mtmfft.mtmfft`
             (Multi-)tapered Fourier analysis

    """

    COV = np.cov(trl_dat, rowvar=False)

# # main diagonal: the auto spectra
# # has shape (nChannels x nFreq)        
# diag = CSD_ij.diagonal()
# # get the needed product pairs of the autospectra
# Ciijj = np.sqrt(diag[:, :, None] * diag[:, None, :]).T
# CSD_ij = CSD_ij / Ciijj



