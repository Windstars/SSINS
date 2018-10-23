"""
Some useful functions specifically involving INS analysis.
"""

from __future__ import absolute_import, division, print_function

from SSINS import util, INS


def INS_concat(INS_data_sequence, axis, freq_sequence=None, metadata_kwargs={}):
    """
    This function is used to concatenate spectra. For instance, if polarizations
    are in separate files or if different parts of the observing band are in
    separate files.
    """
    data = np.concatenate(INS_sequence, axis=axis)
    # This is the frequency axis
    if axis is 2:
        freq_array = np.concatenate(freq_sequence, axis=1)
    ins = INS(data=data, freq_array=freq_array, **metadata_kwargs)

    return(ins)