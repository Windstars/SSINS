"""
A library of wrappers which call plotting functions in the SSINS.plot_lib
library. Each function is named according to the class that they plot.
"""

from __future__ import absolute_import, division, print_function

import os
import numpy as np
from SSINS import util


pol_dict_keys = np.arange(-8, 5)
pol_dict_keys = np.delete(pol_dict_keys, 0)
pol_dict_values = ['YX', 'XY', 'YY', 'XX', 'LR', 'RL', 'LL', 'RR', 'pI', 'pQ', 'pU', 'pV']
pol_dict = dict(zip(pol_dict_keys, pol_dict_values))


def INS_plot(INS, outdir, xticks=None, yticks=None, vmin=None, vmax=None,
             events=False, ms_vmin=None, ms_vmax=None, data_cmap=None,
             xticklabels=None, yticklabels=None, aspect='auto', units='arbs',
             file_ext='png', title=''):

    """Takes an INS and plots its relevant data products. Saves the plots out
    in INS.outpath

    Args:
        INS (INS): The INS whose data is to be plotted. *Required*
        xticks (sequence): The frequency channel indices to tick in INS waterfall plots.
        yticks (sequence): The time indices to tick in INS waterfall plots.
        vmin (float): The minimum of the colormap for the INS (non-mean-subtracted)
        vmax (float): The maximum of the colormap for the INS (non-mean-subtracted)
        events (bool): Set to True to plot histograms of events between flagging iterations. Default is False.
        ms_vmin (float): The minimum of the colormap for the mean-subtracted INS
        ms_vmax (float): The maximum of the colormap for the mean-subtracted INS
        data_cmap (colormap): The colormap for the non-mean-subtracted data
        xticklabels (sequence of str): The labels for the frequency ticks
        yticklabels (sequence of str): The labels for the time ticks
        zero_mask (bool): Set to True if zero'd data points ought to be masked. Default is False.
        aspect (float or 'auto'): Set the aspect ratio of the waterfall plots.
        sig_thresh (str): Used to tag the output plots with the sig_thresh used in flagging.
    """

    from matplotlib import cm
    import matplotlib.pyplot as plt

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    if not INS.label:
        raise ValueError("The INS object does not have a label. The plots will not "
                         "be able to be saved. Aborting plotting.")

    im_kwargs = {'xticks': xticks,
                 'yticks': yticks,
                 'xticklabels': xticklabels,
                 'yticklabels': yticklabels,
                 'aspect': aspect}

    data_kwargs = [{'cbar_label': 'Amplitude (%s)' % (units),
                    'mask_color': 'white',
                    'vmin': vmin,
                    'vmax': vmax,
                    'cmap': data_cmap},
                   {'cbar_label': 'Deviation ($\hat{\sigma}$)',
                    'mask_color': 'black',
                    'cmap': cm.coolwarm,
                    'vmin': ms_vmin,
                    'vmax': ms_vmax}]

    fig, ax = plt.subplots(nrows=INS.metric_array.shape[3],
                           ncols=2, squeeze=False)
    fig.suptitle('%s Incoherent Noise Spectrum' % INS.label)
    for i, data in enumerate(['array', 'ms']):
        im_kwargs.update(data_kwargs[i])
        for pol_ind in range(INS.metric_array.shape[3]):
            ax.imshow(data, )
            image_plot(fig, ax[pol_ind, i],
                       getattr(INS, 'metric_%s' % (string))[:, 0, :, pol_ind],
                       title=pol_dict[INS.polarization_array[pol_ind]],
                       **im_kwargs)
    fig.savefig('%s/%s_INS_data.%s' %
                (outdir, INS.label, file_ext))
    plt.close(fig)

    fig, ax = plt.subplots()
    x = INS.bins[:-1] + 0.5 * np.diff(INS.bins)
    error_plot(fig, ax, x, INS.counts, xlabel='Deviation ($\hat{\sigma}$)',
               title='%s Incoherent Noise Spectrum Histogram' % (INS.obs),
               legend=False)
    fig.savefig('%s/figs/%s_%s_INS_hist%s.png' % (INS.outpath, INS.obs, INS.flag_choice, tag))
    plt.close(fig)


def VDH_plot(SS, outpath, file_label, file_ext='.png', xlabel='',
             xscale='linear', title='', bins='auto', legend=True, yscale='log',
             ylim=None, density=False, pre_flag=True, post_flag=True,
             pre_model=True, post_model=True):

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    fig, ax = plt.subplots()

    if pre_model or post_model:
        model_func = SS.mixture_prob
    else:
        model_func = None

    if post_flag and SS.flag_choice is not None:
        hist_plot(fig, ax, np.abs(SS.data_array[np.logical_not(SS.data_array.mask)]),
                  bins=bins, legend=legend, model_function=model_func,
                  yscale=yscale, ylim=ylim, density=density, label='Post Flag')
    if pre_flag and SS.flag_choice is not None:
        if SS.flag_choice is not 'original':
            temp_flags = np.copy(SS.data_array.mask)
            temp_choice = '%s' % SS.flag_choice
        else:
            temp_choice = 'original'
        SS.apply_flags(flag_choice=None)
        hist_plot(fig, ax, np.abs(SS.data_array).flatten(), bins=bins,
                  legend=legend, model_function=model_func, yscale=yscale,
                  ylim=ylim, density=density, label='Pre Flag')
        if temp_choice is 'original':
            SS.apply_flags(flag_choice='original')
        else:
            SS.apply_flags(flag_choice='custom', custom=temp_flags)
            SS.flag_choice = temp_choice

    fig.savefig('%s/%s_VDG.%s' % (outdir, file_label, file_ext))
