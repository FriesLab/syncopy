# -*- coding: utf-8 -*-
#
# Simple script for testing Syncopy w/o pip-installing it
#

# Builtin/3rd party package imports
import numpy as np

# Add SynCoPy package to Python search path
import os
import sys
spy_path = os.path.abspath(".." + os.sep + "..")
if spy_path not in sys.path:
    sys.path.insert(0, spy_path)

# Import package
import syncopy as spy

# Import artificial data generator
from syncopy.tests.misc import generate_artificial_data
from syncopy.tests import synth_data

from pynwb import NWBHDF5IO


# Prepare code to be executed using, e.g., iPython's `%run` magic command
if __name__ == "__main__":

    mock_up = np.ones((10, 2))
    ad1 = spy.AnalogData([2 * mock_up, mock_up])

    cs1 = spy.connectivityanalysis(ad1)

    cs1.show(channel_i = 0, channel_j = 1).shape
    # cs1.show(channels_i = [0], channels_j = [1]).shape


    sys.exit()

    nwbFilePath = "/home/fuertingers/Documents/job/SyNCoPy/Data/tt2.nwb"
    # nwbFilePath = "/home/fuertingers/Documents/job/SyNCoPy/Data/test.nwb"

    xx = spy.load_nwb(nwbFilePath)


    # nwbio = NWBHDF5IO(nwbFilePath, "r", load_namespaces=True)
    # nwbfile = nwbio.read()

    # AR(2) Network test data
    AdjMat = synth_data.mk_RandomAdjMat(nChannels)
    trls = [100 * synth_data.AR2_network(AdjMat) for _ in range(nTrials)]
    tdat1 = spy.AnalogData(trls, samplerate=fs)

    # phase difusion test data
    f1, f2 = 10, 40
    trls = []
    for _ in range(nTrials):

        p1 = synth_data.phase_diffusion(f1, eps=.01, nChannels=nChannels, nSamples=nSamples)
        p2 = synth_data.phase_diffusion(f2, eps=0.001, nChannels=nChannels, nSamples=nSamples)
        trls.append(
            1 * np.cos(p1) + 1 * np.cos(p2) + 0.6 * np.random.randn(
                nSamples, nChannels))

    tdat2 = spy.AnalogData(trls, samplerate=1000)


    # Test stuff within here...
    data1 = generate_artificial_data(nTrials=5, nChannels=16, equidistant=False, inmemory=False)
    data2 = generate_artificial_data(nTrials=5, nChannels=16, equidistant=True, inmemory=False)



    # client = spy.esi_cluster_setup(interactive=False)
    # data1 + data2

    # sys.exit()
    # spec = spy.freqanalysis(artdata, method="mtmfft", taper="dpss", output="pow")


