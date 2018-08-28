from __future__ import division, print_function, absolute_import

from SSINS import util
from SSINS.data import DATA_PATH
import nose.tools as nt
import os
import numpy as np
import scipy.stats


def test_obslist():
    obsfile = os.path.join(DATA_PATH, 'obs_list.txt')
    obslist_test = ['1061313008', '1061313128', '1061318864', '1061318984']
    obslist = util.make_obslist(obsfile)
    nt.eq_(obslist_test, obslist)


def test_match_fraction():
    # Make up a simple event list belonging to some fictitious data with 5 times and 100 frequencies
    events = np.array([(1, 0, slice(0, 10)), (2, 0, slice(0, 10)), (3, 0, slice(10, 20))])
    Ntimes = 5
    Nfreqs = 100
    # Make the event_fraction dictionary
    event_frac = util.event_fraction(events, Nfreqs, Ntimes)
    nt.ok_(event_frac == {(0, 10): 2 / 5, (10, 20): 1 / 5})


def test_chisq():
    # Use bins that are typical in match_filter case
    bins = np.arange(-4, 5)
    # Make up some counts
    counts = np.array([1, 2, 5, 10, 10, 5, 2, 1])
    # Check default settings
    stat, p = util.chisq(counts, bins)
    # These happen to be the answers
    nt.ok_(np.allclose((stat, p), (3.476106234440926, 0.06226107945215504)))
    # Check expected counts weighting
    stat, p = util.chisq(counts, bins, weight='exp', thresh=5)
    # These happen to be the answers
    nt.ok_(np.allclose((stat, p), (2.6882672697527807, 0.1010896885610924)))