
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

import os
import sys
import importlib
import pkgutil
import logging
from argparse import ArgumentParser

# Import util for propper logging format.
import repyducible.util

def pkg_demo(pkg_name, args):
    pkg = importlib.import_module("%s" % pkg_name)
    Experiment = pkg.Experiment

    data_pkg = importlib.import_module("%s.data" % pkg_name)
    pth = data_pkg.__path__
    data_modules = {}
    for _,name,_ in pkgutil.iter_modules(pth):
        data_modules[name] = "%s.data.%s" % (pkg_name, name)

    mod_pkg = importlib.import_module("%s.models" % pkg_name)
    pth = mod_pkg.__path__
    model_modules = {}
    for _,name,_ in pkgutil.iter_modules(pth):
        model_modules[name] = "%s.models.%s" % (pkg_name, name)

    return modules_demo(Experiment, data_modules, model_modules, args)

def modules_demo(Experiment, data_modules, model_modules, args):
    if 'DISPLAY' in os.environ and len(args) == 0:
        from repyducible.gui import args_gui
        args_gui(Experiment, data_modules, model_modules)
        return

    parser = ArgumentParser(prog='demo', description="See README.md.")
    parser.add_argument('dataset', metavar='DATASET',
                        choices=data_modules.keys(),
                        help='One of the available datasets: %s.' \
                              % ", ".join(data_modules.keys()))
    parser.add_argument('model', metavar='MODEL',
                        choices=model_modules.keys(),
                        help='One of the available models: %s.' \
                              % ", ".join(model_modules.keys()))
    parser.add_argument('params', metavar='PARAMS', nargs='...',
                        help='Params for this experiment. '
                             'For more information, specify DATASET and MODEL '
                             'and add --help to your command line.')
    pargs = parser.parse_args(args)

    model_module = importlib.import_module(model_modules[pargs.model])
    data_module = importlib.import_module(data_modules[pargs.dataset])
    exp = Experiment(data_module.Data, model_module.Model, pargs.params)
    logging.info("Applying model '%s' to dataset '%s'." \
                 % (pargs.model, pargs.dataset))
    exp.run()
    return exp
