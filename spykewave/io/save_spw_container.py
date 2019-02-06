# save_spw_container.py - Save BaseData objects on disk
# 
# Created: February  5 2019
# Last modified by: Stefan Fuertinger [stefan.fuertinger@esi-frankfurt.de]
# Last modification time: <2019-02-06 16:13:09>

# Builtin/3rd party package imports
import os
import json
import numpy as np
from hashlib import blake2b
from numpy.lib.format import open_memmap  

# Local imports
from spykewave.utils import spw_io_parser, SPWIOError, SPWTypeError
from spykewave.datatype import BaseData
from spykewave.io import hash_file

__all__ = ["save_spw"]

# Define SpykeWave's general file-/directory-naming conventions
FILE_EXT = {"out" : "spw",
            "json" : "info",
            "data" : "dat",
            "seg" : "seg"}

##########################################################################################
def save_spw(out_name, out, fname=None):
    """
    Docstring coming soon...
    """

    # Make sure `out_name` is a writable filesystem-location and format it
    if not isinstance(out_name, str):
        raise SPWTypeError(out_name, varname="out_name", expected="str")
    out_base, out_ext = os.path.splitext(out_name)
    if out_ext != FILE_EXT["out"]:
        out_name += "." + FILE_EXT["out"]
    out_name = os.path.abspath(out_name)
    if not os.path.exists(out_name):
        try:
            os.makedirs(out_name)
        except:
            raise SPWIOError(out_name)
    else:
        if not os.path.isdir(out_name):
            raise SPWIOError(out_name)

    # Make sure `out` is a `BaseData` instance
    if not isinstance(out, BaseData):
        raise SPWTypeError(out, varname="out", expected="SpkeWave BaseData object")

    # Assign default value to `fname` or ensure validity of provided file-name
    if fname is None:
        fname = os.path.splitext(os.path.basename(out_name))[0]
    else:
        try:
            spw_io_parser(fname, varname="filename", isfile=True, exists=False)
        except Exception as exc:
            raise exc
        fbase, fext = os.path.splitext(fname)
        if fext in FILE_EXT:
            fname = fbase

    # Use a random salt to construct a hash for differentiating file-names
    fname_hsh = blake2b(digest_size=2, salt=os.urandom(blake2b.SALT_SIZE)).hexdigest()
    filename = os.path.join(out_name, fname + "." + fname_hsh + "." + "{ext:s}")

    # Start by writing segment-related information
    with open(filename.format(ext=FILE_EXT["seg"]), "wb") as out_seg:
        np.save(out_seg, out.trialinfo, allow_pickle=False)
    
    # Get hierarchically "highest" dtype of chunks present in `out`
    dtypes = []
    for data in out._chunks._data:
        dtypes.append(data.dtype)
    out_dtype = np.max(dtypes)
    
    # Allocate target memmap (a npy file) for saving
    dat = open_memmap(filename.format(ext=FILE_EXT["data"]),
                      mode="w+",
                      dtype=out_dtype,
                      shape=out._chunks.shape)
    
    # Point target to source memmaps and force-write by deleting `dat`
    dat = out._chunks
    del dat

    # Compute checksums of created binary files
    seg_hsh = hash_file(filename.format(ext=FILE_EXT["seg"]))
    dat_hsh = hash_file(filename.format(ext=FILE_EXT["data"]))

    # Write to log already here so that the entry is saved in json
    out.log = "Wrote files " + filename.format(ext="[dat/info/seg]")

    # Assemble dict for JSON output
    out_dct = {}
    for attr in ["hdr", "cfg", "notes"]:
        if hasattr(out, attr):
            dct = getattr(out, attr)
            _dict_converter(dct)
            out_dct[attr] = dct
    out_dct["label"] = out.label
    out_dct["segmentlabel"] = out.segmentlabel
    out_dct["log"] = out._log
    out_dct["seg_checksum"] = seg_hsh
    out_dct["dat_checksum"] = dat_hsh

    # Finally, write JSON
    with open(filename.format(ext=FILE_EXT["json"]), "w") as out_json:
        json.dump(out_dct, out_json, indent=4)
              
    return

##########################################################################################
def _dict_converter(dct, firstrun=True):
    """
    Convert all value in dictionary to strings

    Also works w/ nested dict of dicts and is cycle-save, i.e., it can
    handle self-referencing dictionaires. For instance, consider a nested dict 
    w/ back-edge (the dict is no longer an n-ary tree):

    dct = {}
    dct["key1"] = {}
    dct["key1"]["key1.1"] = 3
    dct["key2"]  = {}
    dct["key2"]["key2.1"] = 4000
    dct["key2"]["key2.2"] = dct["key1"]
    dct["key2"]["key2.3"] = dct

    Here, key2.2 points to the dict of key1 and key2.3 is a self-reference. 

    https://stackoverflow.com/questions/10756427/loop-through-all-nested-dictionary-values
    """
    global visited
    if firstrun:
        visited = set()
    for key, value in dct.items():
        if isinstance(value, dict):
            if key not in visited:
                visited.add(key)
                _dict_converter(dct[key], firstrun=False)
        else:
            if hasattr(value, "item"):
                value = value.item()
            dct[key] = value
    return
