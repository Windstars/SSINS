from __future__ import absolute_import, division, print_function

import os
import numpy as np
from SSINS import image_plot, error_plot
from SSINS import util
from matplotlib import cm, use
use('Agg')
import matplotlib.pyplot as plt


def INS_plot(INS, xticks=None, yticks=None, vmin=None, vmax=None,
             xticklabels=None, yticklabels=None, zero_mask=False, aspect=None):
    """
    Takes a noise spectrum and plots its relevant data products.
    Image Plots: Data/Mean-Subtracted Data
    Histograms: Mean-Subtracted Data/Events
    """

    if not os.path.exists('%s/figs' % (INS.outpath)):
        os.makedirs('%s/figs' % (INS.outpath))

    im_kwargs = {'xticks': xticks,
                 'yticks': yticks,
                 'vmin': vmin,
                 'vmax': vmax,
                 'xticklabels': xticklabels,
                 'yticklabels': yticklabels,
                 'zero_mask': zero_mask,
                 'aspect': aspect}

    suptitles = ['%s Incoherent Noise Spectrum' % (INS.obs),
                 '%s Mean-Subtracted Incoherent Noise Spectrum' % (INS.obs)]

    data_kwargs = [{'cbar_label': 'Amplitude (%s)' % (INS.vis_units),
                    'mask_color': 'white'},
                   {'cbar_label': 'Deviation ($\hat{\sigma}$)',
                    'mask_color': 'black',
                    'cmap': cm.coolwarm}]

    tags = ['match', 'chisq', 'samp_thresh']
    tag = ''
    for subtag in tags:
        if len(getattr(INS, '%s_events' % (subtag))):
            tag += '_%s' % subtag

    for i, string in enumerate(['', '_ms']):
        for spw in range(INS.data.shape[1]):
            fig, ax = plt.subplots(figsize=(14, 8), nrows=INS.data.shape[3])
            if type(ax) is not np.ndarray:
                ax = np.array([ax])
            fig.suptitle('%s, spw%i' % (suptitles[i], spw))
            im_kwargs.update(data_kwargs[i])
            for pol in range(INS.data.shape[3]):
                image_plot(fig, ax[pol],
                           getattr(INS, 'data%s' % (string))[:, spw, :, pol],
                           title=INS.pols[pol], freq_array=INS.freq_array[spw],
                           **im_kwargs)
            plt.tight_layout()
            fig.savefig('%s/figs/%s_spw%i_%s_INS%s%s.png' %
                        (INS.outpath, INS.obs, spw, INS.flag_choice, string, tag))
            plt.close(fig)

    for i, string in enumerate(['match_', 'chisq_']):
        if len(getattr(INS, '%shists' % (string))):
            for k, hist in enumerate(getattr(INS, '%shists' % string)):
                fig, ax = plt.subplots(figsize=(14, 8))
                exp, var = util.hist_fit(hist[0], hist[1])
                x = hist[1][:-1] + 0.5 * np.diff(hist[1])
                error_plot(fig, ax, x, hist[0], xlabel='Deviation ($\hat{\sigma}$)')
                error_plot(fig, ax, x, exp, yerr=np.sqrt(var), xlabel='Deviation ($\hat{\sigma}$)')
                fig.savefig('%s/figs/%s_spw%i_f%i_f%i_%sevent_hist_%i.png' %
                            (INS.outpath, INS.obs, getattr(INS, '%sevents' % string)[k][0],
                             getattr(INS, '%sevents' % string)[k][1].indices(INS.data.shape[2])[0],
                             getattr(INS, '%sevents' % string)[k][1].indices(INS.data.shape[2])[1], string, k))
                plt.close(fig)


def MF_plot(MF, xticks=None, yticks=None, vmin=None, vmax=None,
            xticklabels=None, yticklabels=None, zero_mask=False, aspect=None):

    INS_plot(MF.INS, xticks=None, yticks=None, vmin=None, vmax=None,
             xticklabels=None, yticklabels=None, zero_mask=False, aspect=None)


def VDH_plot(VDH, xticks=None, yticks=None, vmin=None, vmax=None,
             xticklabels=None, yticklabels=None, aspect=None):
    """
    Takes a visibility difference histogram and plots it.
    """

    im_kwargs = {'xticks': xticks,
                 'yticks': yticks,
                 'vmin': vmin,
                 'vmax': vmax,
                 'xticklabels': xticklabels,
                 'yticklabels': yticklabels,
                 'aspect': aspect,
                 'cbar_label': '# Baselines',
                 'zero_mask': True,
                 'mask_color': 'white'}

    hist_kwargs = {'counts': {},
                   'fits': {}}

    labels = {'counts': ['All Measurements', 'Measurements, %s Flags' % (VDH.flag_choice)],
              'fits': ['All Fit', 'Fit, %s Flags' % (VDH.flag_choice)]}

    fit_tags = ['All', 'Flags']

    for spw in range(len(VDH.counts) // len(VDH.MLEs)):
        for i in range(1 + bool(VDH.flag_choice)):
            if hasattr(VDH, W_hist):
                fig, ax = plt.subplots(figsize=(14, 8), nrows=(1 + len(VDH.pols)))
            else:
                fig, ax = plt.subplots(figsize=(14, 8))
                ax = [ax, ]
            fig.suptitle('%s Visibility Difference Histogram, spw%i, %s' %
                         (obs, spw, labels['counts'][i]))
            x = []
            for k in range(1 + bool(VDH.flag_choice)):
                x = VDH.bins[spw, k][:-1] + 0.5 * np.diff(VDH.bins[spw, k])
                for attr in ['counts', 'fits']:
                    if hasattr(VDH, attr):
                        if attr is 'fits':
                            hist_kwargs['fits']['yerr'] = VDH.errors[spw, k]
                        error_plot(fig, ax[0], x, getattr(VDH, attr)[spw, k],
                                   xlabel='Amplitude (%s)' % (VDH.vis_units),
                                   label=labels[attr][k], **hist_kwargs[attr])
            if hasattr(VDH, W_hist):
                for pol in range(len(VDH.pols)):
                    image_plot(fig, ax[pol + 1], VDH.W_hist[i][:, spw, :, pol],
                               title=VDH.pols[pol], freq_array=VDH.freq_array[spw],
                               **im_kwargs)
            fig.savefig('%s/figs/%s_spw%i_%s_VDH.png' %
                        (VDH.outpath, obs, spw, fit_tags[i]))
            plt.close(fig)


def ES_plot(ES, xticks=None, yticks=None, xticklabels=None, yticklabels=None,
            zero_mask=False, mask_color='white', aspect=None, vmin=None, vmax=None):

    im_kwargs = {'vmin': vmin,
                 'vmax': vmax,
                 'xlabel': '$\lambda u$ (m)',
                 'ylabel': '$\lambda v$ (m)',
                 'cbar_label': 'Amplitude (%s)' % (ES.vis_units),
                 'xticks': xticks,
                 'yticks': yticks,
                 'xticklabels': xticklabels,
                 'yticklabels': yticklabels,
                 'zero_mask': zero_mask,
                 'mask_color': mask_color,
                 'aspect': aspect}

    hist_labels = ['Measurements', 'Fit']
    fig_tags = ['hist', 'grid']

    if ES.events is not None and len(ES.events):
        for i, event in enumerate(ES.events):
            title_tup = (ES.obs,
                         ES.freq_array[event[0], event[1].indices(len(ES.freq_array[0]))[0]] * 10 ** (-6),
                         ES.freq_array[event[0], event[1].indices(len(ES.freq_array[0]))[1] - 1] * 10 ** (-6),
                         event[2])
            yerr = [None, ES.exp_error[i]]
            fig_hist, ax_hist = plt.subplots(figsize=(14, 8))
            fig_im, ax_im = plt.subplots(figsize=(14, 8), nrows=len(ES.pols))
            if type(ax_im) is not np.ndarray:
                ax_im = np.array([ax_im])
            fig_im.suptitle('%s Event-Averaged Grid, f%.2f Mhz - f%.2f Mhz, t%i' %
                            title_tup)
            x = ES.bins[i][:-1] + 0.5 * np.diff(ES.bins[i])
            for k, string in enumerate(['', 'exp_']):
                error_plot(fig_hist, ax_hist, x, getattr(ES, '%scounts' % (string))[i],
                           xlabel='Amplitude (%s)' % (ES.vis_units),
                           label=hist_labels[k], yerr=yerr[k],
                           title='%s Event-Averaged Histogram, f%.2f Mhz - f%.2f Mhz, t%i' %
                           title_tup)
            for cut in ES.cutoffs[i]:
                ax_hist.axvline(x=cut, color='black')
            for k in range(len(ES.pols)):
                image_plot(fig_im, ax_im[k], ES.uv_grid[i][k], title=ES.pols[k],
                           **im_kwargs)

            fig_hist.savefig('%s/figs/%s_hist_%i.png' % (ES.outpath, ES.obs, i))
            fig_im.savefig('%s/figs/%s_grid_%i.png' % (ES.outpath, ES.obs, i))
            plt.close(fig_hist)
            plt.close(fig_im)
    else:
        print('No events in ES class. Not making plots.')