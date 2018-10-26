
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

class Data(object):
    name = ""
    default_params = {
        'model': {},
        'solver': {},
        'plot': {},
    }

    def __init__(self, seed=None):
        if seed is not None:
            np.random.seed(seed=seed)

    def apply_default_params(self, params):
        defpall = self.default_params['model'].get('*', {})
        defp = self.default_params['model'].get(params['model_name'], {})
        params['model'].update(defpall)
        params['model'].update(defp)

        defps = self.default_params['solver'].get(params['solver_name'], {})
        defpall = defps.get('*', {})
        defp = defps.get(params['model_name'], {})
        params['solver'].update(defpall)
        params['solver'].update(defp)

        params['plot'].update(self.default_params['plot'])
