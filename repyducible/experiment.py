
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

import logging
import os
import pickle
import glob
from datetime import datetime
from argparse import ArgumentParser

from repyducible.util import output_dir_name, output_dir_create, add_log_file,\
                             backup_source, data_from_file, get_params, \
                             DictAction, ValidatedDictAction

class Experiment(object):
    name = ""
    extra_source_files = []

    def __init__(self, DataClass, ModelClass, args):
        self.DataClass = DataClass
        self.ModelClass = ModelClass
        valid_data_params = get_params(self.DataClass)
        valid_data_params_str = ", ".join(valid_data_params)
        valid_model_params = get_params(self.ModelClass)
        valid_model_params.remove("data")
        valid_model_params_str = ", ".join(valid_model_params)

        parser = ArgumentParser(prog='', description="See README.md.")
        parser.add_argument('--output', metavar='OUTPUT_DIR',
                            default='', type=str,
                            help="Path to output directory. "
                                   + "Existing data will be loaded and used.")
        parser.add_argument('--resume', action="store_true", default=False,
                            help="Continue at last state.")
        parser.add_argument('--plot', metavar='PLOT_MODE', default="show",
                            type=str, help="Plot mode (show|hide|no).")
        parser.add_argument('--data-params', metavar='PARAMS',
                            default={}, type=str,
                            action=ValidatedDictAction(valid_data_params),
                            help="Parameters to be passed to the data generator. "
                                 "Valid parameters: %s" % valid_data_params_str)
        parser.add_argument('--model-params', metavar='PARAMS',
                            default={}, type=str,
                            action=ValidatedDictAction(valid_model_params),
                            help="Parameters to be applied to the model. "
                                 "Valid parameters: %s" % valid_model_params_str)
        parser.add_argument('--solver', metavar='SOLVER', default="pdhg",
                            type=str, help="Solver engine (pdhg|cvx).")
        parser.add_argument('--solver-params', metavar='PARAMS',
                            default={}, type=str, action=DictAction,
                            help="Parameters to be passed to the solver engine.")
        parser.add_argument('--snapshots', action="store_true", default=False,
                            help="Store snapshots of solver iteration. "
                                 "Only available for pdhg solver.")
        parser.add_argument('--test', action="store_true", default=False,
                            help="Run PDHG model tests.")
        self.pargs = parser.parse_args(args)

        if self.pargs.output == '':
            self.output_dir = "%s-%s" % (DataClass.name, ModelClass.name)
            self.output_dir = output_dir_name(self.output_dir)
        else:
            self.output_dir = self.pargs.output

        output_dir_create(self.output_dir)
        add_log_file(logging.getLogger(), self.output_dir)
        backup_source(self, self.output_dir, extra=self.extra_source_files)
        logging.debug("Args: %s" % args)

        self.init_params()
        self.restore_data()
        self.restore_params()

    def init_params(self):
        self.params = {
            'data_name': self.DataClass.name, 'data': {},
            'model_name': self.ModelClass.name, 'model': {},
            'solver_name': self.pargs.solver, 'solver': {},
            'plot': {}
        }

    def restore_params(self):
        self.params_file = os.path.join(self.output_dir, 'params.pickle')
        params = data_from_file(self.params_file, format="pickle")
        if params is not None:
            self.params.update(params)

    def restore_data(self):
        self.params['data'].update(self.pargs.data_params)
        self.data_file = os.path.join(self.output_dir, 'data.pickle')
        self.data = data_from_file(self.data_file, format="pickle")
        if self.data is None:
            self.data = self.DataClass(**self.params['data'])
            with open(self.data_file, 'wb') as f:
                pickle.dump(self.data, f)
        self.data.apply_default_params(self.params)

    def run(self):
        self.params['model'].update(self.pargs.model_params)
        self.params['solver'].update(self.pargs.solver_params)
        with open(self.params_file, 'wb') as f:
            pickle.dump(self.params, f)

        self.model = self.ModelClass(self.data, **self.params['model'])

        self.result_file = os.path.join(self.output_dir, 'result.pickle')
        self.result = data_from_file(self.result_file, format="pickle")

        if self.result is not None:
            self.params['solver']['continue_at'] = self.result['data']

        if self.result is None or self.pargs.resume:
            self.model.setup_solver(self.pargs.solver)
            if self.pargs.test and self.pargs.solver == "pdhg":
                self.model.run_pdhg_tests()
            params = self.params['solver']
            if self.pargs.snapshots:
                params = dict(params, cbfun=self.store_snapshot)
            details = self.model.solve(params)
            self.result = {
                'data': self.model.state,
                'details': details,
            }
            with open(self.result_file, 'wb') as f:
                pickle.dump(self.result, f)

        self.snapshots = []
        if self.pargs.snapshots:
            snapshot_path = os.path.join(self.output_dir, "snapshot-*.pickle")
            for snap in sorted(glob.glob(snapshot_path)):
                self.snapshots.append(data_from_file(snap, format="pickle"))

        self.postprocessing()
        self.plot()

    def store_snapshot(self, i, state, info):
        outfile = os.path.join(self.output_dir, "snapshot-%s-%d.pickle"
            % (datetime.now().strftime('%Y%m%d%H%M%S'), i))
        outdata = { 'data': self.model.post(state), 'details': info }
        with open(outfile, 'wb') as f:
            pickle.dump(outdata, f)

    def postprocessing(self): pass
    def plot(self): pass
