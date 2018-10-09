
# This file is part of Repyducible
#
# Copyright 2018 Thomas Vogt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
np.set_printoptions(precision=4, linewidth=200, suppress=True, threshold=10000)

import sys
import os
import errno
import glob
import zipfile
import pickle
import inspect
import re
import importlib
from datetime import datetime

import logging
class MyFormatter(logging.Formatter):
    def format(self, record):
        th, rem = divmod(record.relativeCreated/1000.0, 3600)
        tm, ts = divmod(rem, 60)
        record.relStrCreated = "% 2d:%02d:%06.3f" % (int(th),int(tm),ts)
        return super(MyFormatter, self).format(record)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(MyFormatter('[%(relStrCreated)s] %(message)s'))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
logging.info("Local time: " + datetime.now().isoformat())

def add_log_file(logger, output_dir):
    """ Utility function for consistent log file names.

    Args:
        logger : an instance of logging.Logger
        output_dir : path to output directory
    """
    log_file = os.path.join(output_dir, "{}-{}.log".format(
        datetime.now().strftime('%Y%m%d%H%M%S'), logger.name
    ))
    ch = logging.FileHandler(log_file)
    ch.setFormatter(MyFormatter('[%(relStrCreated)s] %(message)s'))
    ch.setLevel(logging.DEBUG)
    logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.FileHandler)]
    logger.addHandler(ch)

def output_dir_name(label):
    """ Utility function for consistent output dir names.

    Args:
        label : a string that describes the data stored
    Returns:
        path to output directory
    """
    return "./results/{}-{}".format(
        datetime.now().strftime('%Y%m%d%H%M%S'), label
    )

def output_dir_create(output_dir):
    """ Recursively create the given path's directories.

    Args:
        output_dir : some directory path
    """
    try:
        if sys.version_info[0] == 3:
            os.makedirs(output_dir, exist_ok=True)
        else:
            os.makedirs(output_dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
            pass
        else:
            print("Can't create directory {}!".format(output_dir))
            raise

def data_from_file(path, format="np"):
    """ Load numpy or pickle data from the given file.

    Args:
        path : path to data file
        format : if "pickle", pickle is used to load the data (else numpy is used)
    Returns:
        restored numpy or pickle data
    """
    try:
        if format == "pickle":
            return pickle.load(open(path, 'rb'))
        else:
            return np.load(open(path, 'rb'))
    except:
        return None

def addDirToZip(zipHandle, path, exclude=[]):
    """ Add directory given by `path` to opened zip file `zipHandle`

    From https://stackoverflow.com/a/17020687

    Args:
        zipHandle : a zipfile.ZipFile handle
        path : path to directory
        exclude : list of filenames to exclude
    """

    basePath = path.rstrip("/").rpartition("/")[0] + "/"
    for root, dirs, files in os.walk(path):
        if os.path.basename(root) in exclude:
            continue
        # necessary for empty directories?
        #zipHandle.write(os.path.join(root, "."))
        for file in files:
            filePath = os.path.join(root, file)
            inZipPath = filePath.replace(basePath, "", 1).lstrip("\\/")
            zipHandle.write(filePath, inZipPath)

def backup_source(obj, output_dir, extra=[]):
    obj_pkg = re.sub(r"\..*$", "", inspect.getmodule(obj).__name__)
    pkg_path = importlib.import_module(obj_pkg).__path__[0]
    zip_file = os.path.join(output_dir, "{}-source.zip".format(
        datetime.now().strftime('%Y%m%d%H%M%S')
    ))
    zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
    addDirToZip(zipf, pkg_path, exclude=["__pycache__"])
    for f in sum([glob.glob(extraf) for extraf in extra],[]):
        zipf.write(f)
    zipf.close()
