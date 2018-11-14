
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
import numpy as np

class CvxSolver(object):
    "Wrapper for cvx.Problem for use with PDBaseModel"
    def __init__(self, obj, variables, constraints):
        import cvxpy as cvx
        self.variables = variables
        self.constraints = constraints
        self.objective = obj
        self.prob = cvx.Problem(obj, constraints)
        self.x = np.zeros(sum(v.size for v in self.variables))
        self.y = np.zeros(sum(c.size for c in self.constraints))

    def solve(self, continue_at=None):
        if continue_at is not None:
            self.init_vars(*continue_at)
        self.prob.solve(verbose=True, warm_start=True, solver="MOSEK")
        if self.prob.status not in ["infeasible", "unbounded"]:
            self.x[:] = np.hstack([v.value.ravel() for v in self.variables])
            self.y[:] = np.hstack([c.dual_value.ravel() for c in self.constraints])
        else:
            logging.info("Warning: problem %s" % self.prob.status)
        return { 'objp': self.prob.value, 'status': self.prob.status }

    def init_vars(self, x, y):
        self.x[:x.size] = x[:self.x.size]
        self.y[:y.size] = y[:self.y.size]
        i = 0
        for v in self.variables:
            if i+v.size >= x.size: break
            v.value = x[i:i+v.size].reshape(v.shape)
            i += v.size

    @property
    def state(self):
        return (self.x, self.y)

class PDBaseModel(object):
    "Base class for models that are formulated as saddle-point problems"
    name = ""

    def __init__(self, data):
        self.data = data
        self.x = None
        self.y = None
        self.state = None
        self.pdhg_F = None
        self.pdhg_G = None
        self.pdhg_linop = None
        self.cvx_obj = None
        self.cvx_vars = None
        self.cvx_constr = None
        self.cvx_dual = False

    def setup_solver_cvx(self): pass
    def setup_solver_pdhg(self): pass
    def setup_solver(self, solver_name):
        self.solver_name = solver_name
        if solver_name == "cvx":
            logging.info("Solving using CVX...")
            self.setup_solver_cvx()
            self.solver = CvxSolver(self.cvx_obj, self.cvx_vars, self.cvx_constr)
        else:
            self.setup_solver_pdhg()
            logging.info("Solving using Opymize (PDHG)...")
            from opymize.solvers import PDHG
            self.solver = PDHG(self.pdhg_G, self.pdhg_F, self.pdhg_linop)

    def pre_cvx(self, data): return data
    def pre_pdhg(self, data): return data
    def pre(self, data):
        if self.solver_name == "cvx":
            return self.pre_cvx(data)
        else:
            return self.pre_pdhg(data)

    def post_cvx(self, data): return data
    def post_pdhg(self, data): return data
    def post(self, data):
        if self.solver_name == "cvx":
            return self.post_cvx(data)
        else:
            return self.post_pdhg(data)

    def solve(self, solver_params):
        continue_at = solver_params.get('continue_at', self.state)
        solver_params['continue_at'] = self.pre(continue_at)
        details = self.solver.solve(**solver_params)
        self.state = self.post(self.solver.state)
        return details

    def run_pdhg_tests(self):
        G = self.pdhg_G
        F = self.pdhg_F
        linop = self.pdhg_linop
        from opymize.tools.tests import test_gpu_op, test_adjoint
        test_adjoint(linop)
        for op in [linop, linop.adjoint,
                   G.prox(0.5 + np.random.rand()),
                   F.conj.prox(0.5 + np.random.rand())]:
            test_gpu_op(op)
