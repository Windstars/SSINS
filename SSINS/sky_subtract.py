"""
The sky_subtract (SS) class is defined here. This is the backbone of the analysis
pipeline when working with raw datafiles. It is a subclass of UVData. See UVData
documentation for attributes that are not listed here.
"""
import numpy as np
from pyuvdata import UVData
import scipy.stats
import warnings
import traceback


class SS(UVData):

    """
    Defines the SS class.
    """

    def __init__(self):

        """
        Initializes identically to a UVData object, except for one additional attribute.
        """
        super().__init__()
        self.MLE = None
        """Array of length Nfreqs that stores maximum likelihood estimators for
        each frequency, calculated using the MLE_calc method"""

    def read_data(self, filename, diff=False, flag_choice=None, INS=None, custom=None,
             **kwargs):
        """
        Reads in a file that is compatible with UVData object by first calling
        UVData.read(). See UVData documentation for list of kwargs that can be
        passed to UVData.read()

        Args:
            filename (str or list of str): The filepath(s) to read in.
            diff (bool): If True, and data was read in, then difference the visibilities in time
            flag_choice: Sets flags for the data array on read using apply_flags method.
            INS: An INS object for apply_flags()
            custom: A custom flag array for apply_flags()
            kwargs: Additional kwargs are passed to UVData.read()
        """
        self.read(filename, **kwargs)

        if (self.data_array is not None):
            if diff:
                self.diff()
                self.apply_flags(flag_choice=flag_choice, INS=INS, custom=custom)
            else:
                if flag_choice is not None:
                    warnings.warn("flag_choice will be ignored on read since"
                                  " diff is being skipped.")

    def apply_flags(self, flag_choice=None, INS=None, custom=None):
        """
        A function which applies flags to the data via numpy masked arrays. Also
        changes the SS.flag_choice attribute.

        Args:
            flag_choice (None, 'original', 'INS', 'custom'):
                Applies flags according to the choice. None unflags the data.
                'original' applies flags based on the flag_array attribute.
                'INS' applies flags from an INS object specified by the INS keyword.
                'custom' applies a custom flag array specified by the custom keyword
                - it must be the same shape as the data.
            INS: An INS from which to apply flags - only used if flag_choice='INS'
            custom: A custom flag array from which to apply flags - only used if flag_choice='custom'
        """
        if not isinstance(self.data_array, np.ma.MaskedArray):
            self.data_array = np.ma.masked_array(self.data_array)
        self.flag_choice = flag_choice
        self.MLE = None
        if flag_choice is 'original':
            self.data_array.mask = np.copy(self.flag_array)
        elif flag_choice is 'INS':
            if not np.all(INS.time_array == np.unique(self.time_array)):
                raise ValueError("INS object and SS object have incompatible time arrays. Cannot apply flags.")
            self.data_array.mask[:] = False
            for time_ind, time in enumerate(INS.time_array):
                freq_inds, pol_inds = np.where(INS.metric_array.mask[time_ind])
                # Skip if nothing to flag
                if len(freq_inds) > 0:
                    blt_inds = np.where(self.time_array == time)
                    self.data_array.mask[blt_inds, :, freq_inds, pol_inds] = True
        elif flag_choice is 'custom':
            self.data_array.mask[:] = False
            if custom is not None:
                self.data_array[custom] = np.ma.masked
            else:
                warnings.warn("Custom flags were chosen, but custom flags were None type. Setting flag_choice to None and unmasking data.")
                self.flag_choice = None
        elif flag_choice is None:
            self.data_array.mask = np.zeros(self.data_array.shape, dtype=bool)
        else:
            raise ValueError('flag_choice of %s is unacceptable, aborting.' % flag_choice)

    def diff(self):

        """
        Differences the visibilities in time. Does so independently for each baseline,
        so different integration times or sets of time centers are supported.
        The flags are propagated by taking the boolean OR of the entries that correspond
        to the visibilities that are differenced from one another. Other metadata
        attributes are also adjusted so that the resulting SS object passes
        UVData.check()
        """

        if self.blt_order != 'baseline':
            warnings.warn("Reordering data array to baseline order to perform differencing.")
            self.reorder_blts(order='baseline')

        # index accumulator
        ind_acc = 0
        # Just treat every baseline independently - make no assumptions other than what is guaranteed by baseline ordered objects
        for bl in np.unique(self.baseline_array):
            diff_dat = np.diff(self.get_data(bl, squeeze='none'), axis=0)
            diff_flags = np.logical_or(self.get_flags(bl, squeeze='none')[:-1],
                                       self.get_flags(bl, squeeze='none')[1:])
            diff_times = self.get_times(bl)
            diff_times = 0.5 * (diff_times[:-1] + diff_times[1:])
            diff_nsamples = self.get_nsamples(bl, squeeze='none')
            diff_nsamples = 0.5 * (diff_nsamples[:-1] + diff_nsamples[1:])

            len_diff = diff_dat.shape[0]
            blt_slice = slice(ind_acc, ind_acc + len_diff)

            self.data_array[blt_slice, :, :, :] = diff_dat
            """The time-differenced visibilities. Complex array of shape (Nblts, Nspws, Nfreqs, Npols)."""
            self.flag_array[blt_slice, :, :, :] = diff_flags
            """The flag array, which results from boolean OR of the flags corresponding to visibilities that are differenced from one another."""

            self.time_array[blt_slice] = diff_times
            """The center time of the differenced visibilities. Length Nblts."""
            self.nsample_array[blt_slice, :, :, :] = diff_nsamples
            """See pyuvdata documentation. Here we average the nsample_array of the visibilities that are differenced"""

            where_bl = np.where(self.baseline_array == bl)

            diff_ints = self.integration_time[where_bl]
            diff_ints = diff_ints[:-1] + diff_ints[1:]
            diff_uvw = self.uvw_array[where_bl]
            diff_uvw = 0.5 * (diff_uvw[:-1] + diff_uvw[1:])

            self.integration_time[blt_slice] = diff_ints
            """Total amount of integration time (sum of the differenced visibilities) at each baseline-time (length Nblts)"""
            self.uvw_array[blt_slice] = diff_uvw

            self.baseline_array[blt_slice] = bl
            self.ant_1_array[blt_slice], self.ant_2_array[blt_slice] = self.baseline_to_antnums(bl)
            ind_acc += len_diff

        # Adjust the UVData attributes.
        self.Nblts -= self.Nbls
        """Number of baseline-times. Not necessarily equal to Nbls * Ntimes"""
        self.Ntimes -= 1
        """Total number of integration times in the data. Equal to the original Ntimes-1."""

        for blts_attr in ['data_array', 'flag_array', 'time_array',
                          'nsample_array', 'integration_time', 'baseline_array',
                          'ant_1_array', 'ant_2_array', 'uvw_array']:
            setattr(self, blts_attr, getattr(self, blts_attr)[:-self.Nbls])

        super().set_lsts_from_time_array()
        self.data_array = np.ma.masked_array(self.data_array)

    def MLE_calc(self):

        """
        Calculates maximum likelihood estimators for Rayleigh fits at each
        frequency. Used for developing a mixture fit.
        """

        self.MLE = np.sqrt(0.5 * np.mean(np.absolute(self.data_array)**2, axis=(0, 1, -1)))

    def mixture_prob(self, bins):
        """
        Calculates the probabilities of landing in each bin for a given set of
        bins.

        Args:
            bins: The bin edges of the bins to calculate the probabilities for.
        Returns:
            prob: The probability to land in each bin based on the maximum likelihood model
        """

        if not isinstance(self.data_array, np.ma.MaskedArray):
            self.apply_flags()
        if self.MLE is None:
            self.MLE_calc()
        if bins is 'auto':
            _, bins = np.histogram(np.abs(self.data_array[np.logical_not(self.data_array.mask)]))

        N_spec = np.sum(np.logical_not(self.data_array.mask), axis=(0, 1, -1))
        N_total = np.sum(N_spec)

        # Calculate the fraction belonging to each frequency
        chi_spec = N_spec / N_total

        # initialize the probability array
        prob = np.zeros(len(bins) - 1)
        # Calculate the mixture distribution
        # If this could be vectorized over frequency, that would be better.
        for chan in range(self.Nfreqs):
            if self.MLE[chan] > 0:
                quants = scipy.stats.rayleigh.cdf(bins, scale=self.MLE[chan])
                prob += chi_spec[chan] * (quants[1:] - quants[:-1])

        return(prob)

    def rev_ind(self, band):

        """
        Reverse indexes sky-subtracted visibilities whose amplitudes are within
        a band given by the band argument. Collapses along the baselines to
        return a time-frequency waterfall per polarization. For example, setting
        a band of [1e3, 1e4] reports the number of baselines at each
        time/frequency/polarization whose sky-subtracted visibility amplitude
        was between 1e3 and 1e4. Includes flags.

        Args:
            band: The minimum and maximum amplitudes to be sought
        Returns:
            rev_ind_hist:
                A time-frequency waterfall per polarization counting the number
                of baselines whose sky-subtracted visibility amplitude fell
                within the band argument.

        """

        if not isinstance(self.data_array, np.ma.MaskedArray):
            self.apply_flags()
        where_band = np.logical_and(np.absolute(self.data_array) > min(band),
                                    np.absolute(self.data_array) < max(band))
        where_band_mask = np.logical_and(np.logical_not(self.data_array.mask),
                                         where_band)
        shape = [self.Ntimes, self.Nbls, self.Nfreqs, self.Npols]
        rev_ind_hist = np.sum(where_band_mask.reshape(shape), axis=1)
        return(rev_ind_hist)

    def write(self, filename_out, file_type_out, UV=None, filename_in=None,
              read_kwargs={}, combine=True, nsample_default=1, write_kwargs={}):

        """
        Lets one write out the flags to a new file. This requires extending the
        flags in time. The same convention is used as in INS.flags_to_mask().
        The rest of the data for writing the file is pulled from an existing
        UVData object passed using the UV keyword, or read in to a new UVData
        object using the filename_in keyword. Due to how the nsample_array
        and flag_array get combined into the weights when writing uvfits,
        areas where the nsample_array == 0 are set to nsample_default so that
        new flags can actually be propagated to those data in the new uvfits file.

        Args:
            filename_out: The name of the file to write to. *Required*
            file_type_out: The typle of file to write out. See pyuvdata documentation for options. *Required*
            UV: A UVData object whose data and metadata to use to write the file.
            filename_in: A file from which to read data in order to write the new file. Not used if UV is not None.
            read_kwargs: A keyword dictionary for the UVData read method if reading from a file. See pyuvdata documentation for read keywords.
            combine (bool): If True, combine the original flags with the new flags (OR them), else just use the new flags.
            nsample_default:
                Used for writing uvfits when elements of the nsample_array are 0.
                This is necessary due to the way the nsample_array and flag_array
                are combined into the weights when writing uvfits, otherwise
                flags do not actually get propagated to the new file where nsample_array is 0.
            write_kwargs: A keyword dictionary for the selected UVData write method. See pyuvdata documentation for write keywords.
        """

        if self.blt_order != 'baseline':
            warnings.warn("Reordering data array to baseline order to propagate flags.")
            self.reorder_blts(order='baseline')
        if UV is None:
            UV = UVData()
            UV.read(filename_in, **read_kwargs)

        # Option to keep old flags
        if not combine:
            UV.flag_array[:] = 0

        # Check nsample_array for issue
        if np.any(UV.nsample_array == 0) and (file_type_out is 'uvfits'):
            warnings.warn("Some nsamples are 0, which will result in failure to propagate flags. Setting nsample to default values where 0.")
            UV.nsample_array[UV.nsample_array == 0] = nsample_default

        # index accumulator
        ind_acc = 0
        if UV.blt_order != 'baseline':
            UV.reorder_blts(order='baseline')
        for bl in np.unique(self.baseline_array):
            try:
                uv_times = UV.get_times(bl)
                self_times = self.get_times(bl)
                time_compat = np.all(self_times == 0.5 * (uv_times[:-1] + uv_times[1:]))
                assert time_compat
            except Exception:
                raise ValueError("UVData and SS objects were found to be incompatible."
                                 " Check that the SS and UVData objects were read appropriately!")

            new_flags = self.get_data(bl, squeeze='none').mask
            end_ind = new_flags.shape[0] + 1 + ind_acc
            UV.flag_array[ind_acc:end_ind - 1][new_flags] = 1
            UV.flag_array[ind_acc + 1:end_ind][new_flags] = 1
            ind_acc = end_ind

        # Write file
        getattr(UV, 'write_%s' % file_type_out)(filename_out, **write_kwargs)
