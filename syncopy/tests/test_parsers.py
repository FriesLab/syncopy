# -*- coding: utf-8 -*-
# 
# 
# 
# Created: 2019-03-05 16:22:56
# Last modified by: Stefan Fuertinger [stefan.fuertinger@esi-frankfurt.de]
# Last modification time: <2019-07-23 15:22:22>

import os
import platform
import tempfile
import pytest
import numpy as np
from collections import OrderedDict
from syncopy.shared.parsers import (io_parser, scalar_parser, array_parser, 
                                    filename_parser, data_parser, json_parser)
from syncopy.shared import get_defaults
from syncopy.shared.errors import SPYValueError, SPYTypeError, SPYIOError
from syncopy import AnalogData, SpectralData


class TestIoParser():
    existingFolder = tempfile.gettempdir()
    nonExistingFolder = os.path.join("unlikely", "folder", "to", "exist")

    def test_none(self):
        with pytest.raises(SPYTypeError):
            io_parser(None)

    def test_exists(self):
        io_parser(self.existingFolder, varname="existingFolder",
                  isfile=False, exists=True)
        with pytest.raises(SPYIOError):
            io_parser(self.existingFolder, varname="existingFolder",
                      isfile=False, exists=False)

        io_parser(self.nonExistingFolder, varname="nonExistingFolder",
                  exists=False)

        with pytest.raises(SPYIOError):
            io_parser(self.nonExistingFolder, varname="nonExistingFolder",
                      exists=True)

    def test_isfile(self):
        with tempfile.NamedTemporaryFile() as f:
            io_parser(f.name, isfile=True, exists=True)
            with pytest.raises(SPYValueError):
                io_parser(f.name, isfile=False, exists=True)

    def test_ext(self):
        with tempfile.NamedTemporaryFile(suffix='a7f3.lfp') as f:
            io_parser(f.name, ext=['lfp', 'mua'], exists=True)
            io_parser(f.name, ext='lfp', exists=True)
            with pytest.raises(SPYValueError):
                io_parser(f.name, ext='mua', exists=True)


class TestScalarParser():
    def test_none(self):
        with pytest.raises(SPYTypeError):
            scalar_parser(None, varname="value",
                          ntype="int_like", lims=[10, 1000])

    def test_within_limits(self):
        value = 440
        scalar_parser(value, varname="value",
                      ntype="int_like", lims=[10, 1000])

        freq = 2        # outside bounds
        with pytest.raises(SPYValueError):
            scalar_parser(freq, varname="freq",
                          ntype="int_like", lims=[10, 1000])

    def test_integer_like(self):
        freq = 440.0
        scalar_parser(freq, varname="freq",
                      ntype="int_like", lims=[10, 1000])

        # not integer-like
        freq = 440.5
        with pytest.raises(SPYValueError):
            scalar_parser(freq, varname="freq",
                          ntype="int_like", lims=[10, 1000])

    def test_string(self):
        freq = '440'
        with pytest.raises(SPYTypeError):
            scalar_parser(freq, varname="freq",
                          ntype="int_like", lims=[10, 1000])

    def test_complex_valid(self):
        value = complex(2, -1)
        scalar_parser(value, lims=[-3, 5])  # valid

    def test_complex_invalid(self):
        value = complex(2, -1)
        with pytest.raises(SPYValueError):
            scalar_parser(value, lims=[-3, 1])


class TestArrayParser():

    time = np.linspace(0, 10, 100)

    def test_none(self):
        with pytest.raises(SPYTypeError):
            array_parser(None, varname="time")

    def test_1d_ndims(self):
        # valid ndims
        array_parser(self.time, varname="time", dims=1)

        # invalid ndims
        with pytest.raises(SPYValueError):
            array_parser(self.time, varname="time", dims=2)

    def test_1d_shape(self):
        # valid shape
        array_parser(self.time, varname="time", dims=(100,))

        # valid shape, unkown size
        array_parser(self.time, varname="time", dims=(None,))
        
        # invalid shape
        with pytest.raises(SPYValueError):
            array_parser(self.time, varname="time", dims=(100, 1))

    def test_2d_shape(self):
        # make `self.time` a 2d-array
        dummy = self.time.reshape(10, 10)

        # valid shape
        array_parser(dummy, varname="time", dims=(10, 10))

        # valid shape, unkown size
        array_parser(dummy, varname="time", dims=(10, None))
        array_parser(dummy, varname="time", dims=(None, 10))
        array_parser(dummy, varname="time", dims=(None, None))

        # valid ndim
        array_parser(dummy, varname="time", dims=2)

        # invalid ndim
        with pytest.raises(SPYValueError):
            array_parser(dummy, varname="time", dims=3)

        # invalid shape
        with pytest.raises(SPYValueError):
            array_parser(dummy, varname="time", dims=(100, 1))
        with pytest.raises(SPYValueError):
            array_parser(dummy, varname="time", dims=(None,))
        with pytest.raises(SPYValueError):
            array_parser(dummy, varname="time", dims=(None, None, None))

    def test_1d_newaxis(self):
        # appending singleton dimensions does not affect parsing
        time = self.time[:, np.newaxis]
        array_parser(time, varname="time", dims=(100,))
        array_parser(time, varname="time", dims=(None,))

    def test_1d_lims(self):
        # valid lims
        array_parser(self.time, varname="time", lims=[0, 10])
        # invalid lims
        with pytest.raises(SPYValueError):
            array_parser(self.time, varname="time", lims=[0, 5])

    def test_ntype(self):
        # string
        with pytest.raises(SPYTypeError):
            array_parser(str(self.time), varname="time", ntype="numeric")
        # float32 instead of expected float64
        with pytest.raises(SPYValueError):
            array_parser(np.float32(self.time), varname="time",
                         ntype='float64')

    def test_character_list(self):
        channels = np.array(["channel1", "channel2", "channel3"])
        array_parser(channels, varname="channels", dims=1)
        array_parser(channels, varname="channels", dims=(3,))
        array_parser(channels, varname="channels", dims=(None,))
        with pytest.raises(SPYValueError):
            array_parser(channels, varname="channels", dims=(4,))


class TestFilenameParser():
    referenceResult = {
        "filename": "sessionName_testTag.analog",
        "container": "container.spy",
        "folder": "/tmp/container.spy",
        "tag": "testTag",
        "basename": "sessionName",
        "extension": ".analog"
        }

    def test_none(self):
        assert all([value is None for value in filename_parser(None).values()])

    def test_fname_only(self):
        fname = "sessionName_testTag.analog"         
        assert filename_parser(fname) == {
            "filename" : fname,
            "container": None,
            "folder": os.getcwd(),
            "tag": None,
            "basename": "sessionName_testTag",
            "extension": ".analog"
        }
    
    def test_invalid_ext(self):
        # wrong extension
        with pytest.raises(SPYValueError):
            filename_parser("test.wrongExtension")
        
        # no extension
        with pytest.raises(SPYValueError):
            filename_parser("test")

    def test_with_info_ext(self):
        fname = "sessionName_testTag.analog.info" 
        assert filename_parser(fname) == {
            "filename" : fname.replace(".info", ""),
            "container": None,
            "folder": os.getcwd(),
            "tag": None,
            "basename": "sessionName_testTag",
            "extension": ".analog"
        }

    def test_valid_spy_container(self):
        fname = "sessionName.spy/sessionName_testTag.analog"         
        assert filename_parser(fname, is_in_valid_container=True) == {
            "filename" : "sessionName_testTag.analog",
            "container": "sessionName.spy",
            "folder": os.path.join(os.getcwd(), "sessionName.spy"),
            "tag": "testTag",
            "basename": "sessionName",
            "extension": ".analog"
        }
    def test_invalid_spy_container(self):
        fname = "sessionName/sessionName_testTag.analog"   
        with  pytest.raises(SPYValueError):   
            filename_parser(fname, is_in_valid_container=True)
        
        fname = "wrongContainer.spy/sessionName_testTag.analog"   
        with  pytest.raises(SPYValueError):   
            filename_parser(fname, is_in_valid_container=True)

    def test_with_full_path(self):
        fname = os.path.normpath("/tmp/sessionName.spy/sessionName_testTag.analog")
        folder = "{}/tmp".format("C:" if platform.system() == "Windows" else "")
        assert filename_parser(fname, is_in_valid_container=True) == {
            "filename" : "sessionName_testTag.analog",
            "container": "sessionName.spy",
            "folder": os.path.join(os.path.normpath(folder), "sessionName.spy"),
            "tag": "testTag",
            "basename": "sessionName",
            "extension": ".analog"
            }
    
    def test_folder_only(self):
        assert filename_parser("container.spy") == {
            'filename': None,
            'container': 'container.spy',
            'folder': os.getcwd(),
            'tag': None,
            'basename': 'container',
            'extension': '.spy'
            }
        folder = "{}/tmp".format("C:" if platform.system() == "Windows" else "")
        assert filename_parser("/tmp/container.spy") == {
            'filename': None,
            'container': 'container.spy',
            'folder': os.path.normpath(folder),
            'tag': None,
            'basename': 'container',
            'extension': '.spy'
            }



class TestDataParser():
    data = AnalogData()

    def test_none(self):
        with pytest.raises(SPYTypeError):
            data_parser(None)

    def test_dataclass(self):
        # valid
        data_parser(self.data, dataclass=AnalogData)

        # invalid
        with pytest.raises(SPYTypeError):
            data_parser(self.data, dataclass=SpectralData)

    def test_empty(self):
        with pytest.raises(SPYValueError):
            data_parser(self.data, empty=False)
        self.data.data = np.ones((3, 10))
        data_parser(self.data, empty=False)

    def test_writable(self):
        self.data.mode = "r+"
        data_parser(self.data, writable=True)
        with pytest.raises(SPYValueError):
            data_parser(self.data, writable=False)

    def test_dimord(self):
        with pytest.raises(SPYValueError):
            data_parser(self.data, dimord=["freq", "chan"])


def func(input, keyword=None):
    """ Test function for get_defaults test """
    pass


def test_get_defaults():
    assert get_defaults(func) == {"keyword": None}


def test_json_parser():
    # wanted is subset + order shouldn't matter
    actual = OrderedDict({"entry1": 1, "entry2": "2", "entry99": 99.9})
    wanted = OrderedDict({"entry2": str, "entry1": int})
    json_parser(actual, wanted)
    # not all keys present (`wanted` and `actual` simply swap roles)
    with pytest.raises(SPYValueError):
        json_parser(wanted, actual)
    # key is of wrong type
    actual["entry2"] = 2
    with pytest.raises(SPYTypeError):
        json_parser(actual, wanted)
