import plot_lib as pl
import Util
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

    for i, string in enumerate(['', '_ms']):
        for spw in range(INS.data.shape[1]):
            fig, ax = plt.subplots(figsize=(14, 8), nrows=INS.data.shape[3])
            fig.suptitle('%s, spw%i' % (suptitles[i], spw))
            im_kwargs.update(data_kwargs[i])
            for pol in range(4):
                pl.image_plot(fig, ax[pol],
                              getattr(INS, 'data%s' % (string))[:, spw, :, pol],
                              title=INS.pols[pol], freq_array=INS.freq_array[spw],
                              **im_kwargs)
            fig.savefig('%s/figs/%s_%s_INS%s.png' % (INS.outpath, INS.obs, string))
            plt.close(fig)

    for i, string in enumerate(['match_', 'chisq_']):
        if len(getattr(INS, '%shists' % (string))):
            for k, hist in enumerate(getattr(INS, '%shists')):
                fig, ax = plt.subplots(figsize=(14, 8))
                exp, var = Util.hist_fit(hist[0], hist[1])
                x = hist[1][:-1] + 0.5 * np.diff(hist[1])
                pl.error_plot(fig, ax, x, hist[0], xlabel='Deviation ($\hat{\sigma}$)')
                pl.error_plot(fig, ax, x, exp, yerr=np.sqrt(var), xlabel='Deviation ($\hat{\sigma}$)')
                fig.savefig('%s/figs/%s_spw%i_f%i_f%i_%sevent_hist_%i.png' %
                            (outpath, INS.obs, event[0],
                             event[1].indices(INS.shape[2])[0],
                             event[1].indices(INS.shape[2])[1], string, k))
                plt.close(fig)


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

    for spw in range(len(VDH.counts) / len(VDH.MLEs)):
        for i in range(1 + bool(VDH.flag_choice)):
            if hasattr(VDH, W_hist):
                fig, ax = plt.subplots(figsize=(14, 8), nrows=(1 + len(VDH.pols)))
            else:
                fig, ax = plt.subplots(figsize=(14, 8))
                ax = [ax, ]
            fig.suptitle('%s Visibility Difference Histogram, spw%i, %s' % (obs, spw, labels[i]))
            x = []
            for k in range(1 + bool(VDH.flag_choice)):
                x = VDH.bins[spw, k][:-1] + 0.5 * np.diff(VDH.bins[spw, k])
                for attr in ['counts', 'fits']:
                    if attr is 'fits':
                        hist_kwargs['fits']['yerr'] = VDH.errors[spw, k]
                    pl.error_plot(fig, ax[0], x, getattr(VDH, attr)[spw, k],
                                  xlabel='Amplitude (%s)' % (VDH.vis_units),
                                  label=labels[attr][k], **hist_kwargs[attr])
            if hasattr(VDH, W_hist):
                for pol in range(len(VDH.pols)):
                    pl.image_plot(fig, ax[pol + 1], VDH.W_hist[i][:, spw, :, pol],
                                  title=VDH.pols[pol], freq_array=VDH.freq_array[spw],
                                  **im_kwargs)
            fig.savefig('%s/figs/%s_spw%i_%s_VDH.png' % (VDH.outpath, obs, spw, fit_tags[i]))
            plt.close(fig)


def BA_plot(BA, xticks=None, yticks=None, xticklabels=None, yticklabels=None,
            zero_mask=False, mask_color='white', aspect=None):

    im_kwargs = {'vmin': vmin,
                 'vmax': vmax,
                 'xlabel': '$\lambda u$ (m)',
                 'ylabel': '$\lambda v$ (m)',
                 'cbar_label': 'Amplitude (%s)' % (vis_units),
                 'xticks': xticks,
                 'yticks': yticks,
                 'xticklabels': xticklabels,
                 'yticklabels': yticklabels,
                 'zero_mask': zero_mask,
                 'mask_color': mask_color,
                 'aspect': aspect}

    hist_labels = ['Measurements', 'Fit']
    fig_tags = ['hist', 'grid']

    for i, event in enumerate(BA.events):
        title_tup = (BA.obs,
                     BA.freq_array[event[0], event[1].indices(BA.Nfreqs)[0]] * 10 ** (-6),
                     BA.freq_array[event[0], event[1].indices(BA.Nfreqs)[1]] * 10 ** (-6),
                     event[2])
        yerr = [None, BA.errors[i]]
        fig_hist, ax_hist = plt.subplots(figsize=(14, 8))
        fig_im, ax_im = plt.subplots(figsize=(14, 8), nrows=len(BA.pols))
        fig_im.suptitle('%s Event-Averaged Grid, f%.2f Mhz - f%.2f Mhz, t%i' %
                        title_tup)
        x = BA.bins[i][:-1] + 0.5 * np.diff(BA.bins[i])
        for k, string in enumerate(['', 'exp_']):
            pl.error_plot(fig_hist, ax_hist, x, getattr(BA, '%scounts' % (string))[i],
                          xlabel='Amplitude (%s)' % (BA.vis_units),
                          label=hist_labels[k], yerr=yerr[k],
                          title='%s Event-Averaged Histogram, f%.2f Mhz - f%.2f Mhz, t%i' %
                          title_tup)
        for cut in BA.cutoffs[i]:
            ax_hist.axvline(x=cut, color='black')
        for k in range(len(BA.pols)):
            pl.image_plot(fig_im, ax_im, BA.uv_grid[k], title=BA.pols[k],
                          **im_kwargs)

        fig_hist.savefig('%s/figs/%s_hist_%i.png' % (BA.outpath, BA.obs, i))
        fig_im.savefig('%s/figs/%s_grid_%i.png' % (BA.outpath, BA.obs, i))