
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

import sys
import importlib
import pkgutil
import logging

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
    logging.info("Available datasets: %s" % ", ".join(data_modules.keys()))

    mod_pkg = importlib.import_module("%s.models" % pkg_name)
    pth = mod_pkg.__path__
    model_modules = {}
    for _,name,_ in pkgutil.iter_modules(pth):
        model_modules[name] = "%s.models.%s" % (pkg_name, name)
    logging.info("Available models: %s" % ", ".join(model_modules.keys()))

    return modules_demo(Experiment, data_modules, model_modules, args)

def modules_demo(Experiment, data_modules, model_modules, args):
    if len(args) == 0:
        if len(data_modules.keys()) == 1 and len(model_modules.keys()) == 1:
            data_name = data_modules.keys()[0]
            model_name = model_modules.keys()[0]
        else:
            sys.exit("Error: Please specify a DATASET.")
    elif len(args) < 2:
        if len(model_modules) == 1:
            data_name = args.pop(0)
            model_name = model_modules.keys()[0]
        else:
            sys.exit("Error: Please specify a MODEL.")
    else:
        data_name = args.pop(0)
        model_name = args.pop(0)

    if data_name not in data_modules:
        sys.exit("Error: Unknown dataset '%s'" % data_name)

    if model_name not in model_modules:
        sys.exit("Error: Unknown model '%s'" % model_name)

    logging.info("Applying model '%s' to dataset '%s'." % (model_name, data_name))
    return run_demo(Experiment, data_modules[data_name], model_modules[model_name], args)

def run_demo(Experiment, data_modulename, model_modulename, args):
    model_module = importlib.import_module(model_modulename)
    data_module = importlib.import_module(data_modulename)
    exp = Experiment(data_module.Data, model_module.Model, args)
    exp.run()
    return exp
