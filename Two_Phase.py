import numpy as np
import time

class LP_model_solver(object):
    def __init__(self, vars_name, C, A, RHS, slack_vars, is_min):
        self.vars_name = vars_name
        self.C = np.array(C).astype(np.float64)
        self.A = np.array(A).astype(np.float64)
        self.RHS = np.array(RHS).astype(np.float64)
        self.slack_vars = np.array(slack_vars).astype(np.float64)
        self.is_min = is_min
        self._convert_to_standard_form()
        self._equal_threshold = 1e-6

    def _convert_to_standard_form(self):
        ## convert the original LP to a minimization problem (if not) with standard form
        self.var_num = self.C.size + self.slack_vars.size  # total number of variables
        self.const_num = self.RHS.size # total number of constraints
        # update the cost coefficients
        if not self.is_min:
            self.C = self.C * (-1.0)
        new_C = list(self.C)
        for _ in range(self.slack_vars.size):
            new_C.append(0.0)
        self.C = np.array(new_C).astype(np.float64)
        # update the constraint matrix
        slack_matrix = np.eye(self.slack_vars.size, dtype=np.float64) # identity matrix
        new_A = []
        for i in range(self.const_num):
            new_A.append(np.concatenate([self.A[i], self.slack_vars[i]*slack_matrix[i]]))
        self.A = np.array(new_A).astype(np.float64)

    def _create_init_phase_1_tableau(self):
        # Requirement 4: we introduce artificial variables, and start simplex with them
        # index of the basic and non-basic variables
        self.basis = list(range(self.var_num, (self.var_num + self.const_num)))
        self.non_basis = list(range(self.var_num))
        # now B is an identity matrix, based on which we can build the tableau
        artif_matrix = np.eye(self.const_num, dtype=np.float64) # identity matrix
        self.tableau = []
        # there are in total constraints_num + 1 rows in the tableau
        for row in range(self.const_num):
            # non-artificial, artificial, RHS
            self.tableau.append(np.concatenate([self.A[row], artif_matrix[row],
                                                [self.RHS[row]]]))
        # compute the last row of the tableau
        last_row = np.concatenate([np.sum(self.A, axis=0), np.zeros((self.const_num, )),
                                   [np.sum(self.RHS)]])
        assert last_row.size == self.var_num + self.const_num + 1
        self.tableau.append(last_row)
        self.tableau = np.array(self.tableau).astype(np.float64)

    def _simplex_tableau(self):
        assert self.const_num == len(self.basis)
        iteration = 0
        while any(self.tableau[-1][self.non_basis] > (0 + self._equal_threshold)):
            reduced_cost = self.tableau[-1][self.non_basis]
            enter_axis_idx = np.argmax(reduced_cost)
            enter_axis = self.non_basis[enter_axis_idx]
            y_k = self.tableau[:-1, enter_axis]
            if all(y_k <= (0 + self._equal_threshold)):
                # Requirement 6: termination with unboundness
                rc = self._get_recession_cone(enter_axis, y_k)
                return {'Type': 'unbounded', 'Recession Cone': rc}
            # Requirement 5: one rule to prevent the simplex method from cycling
            leave_axis_idx = self._lexicographic_rule(y_k)
            self._update_tableau(enter_axis_idx, leave_axis_idx) # pivoting
            cur_sol, cur_obj = self._get_result()
            print("Iteration #{}:".format(iteration))
            print("The current objective is {}.".format(cur_obj))
            print("The current solution (basic variable: value) is {}.".format(cur_sol))
            iteration += 1
        # Requirement 6: termination with finite optimal solution
        optimal_solution, optimal_obj = self._get_result()

        return {'Type': 'optimal', 'Optimal Solution': optimal_solution,
                'Optimal Objective': optimal_obj}

    def _get_result(self):
        current_solution = {}
        for row in range(self.const_num):
            current_solution[self.basis[row]] = self.tableau[row][-1]
        current_solution = dict(sorted(current_solution.items(), key=lambda x: x[0]))
        current_obj = self.tableau[-1][-1]
        if not self.is_min:
            current_obj *= -1.0

        return current_solution, current_obj

    def _get_recession_cone(self, enter_axis, y_k):
        # the recession cone 'rc' is saved as a dict {var_idx: (a, b), ...},
        # where rc[var_idx] = a + b * z, z >= 0
        rc = {}
        # basic variables
        for i in range(len(self.basis)):
            rc[self.basis[i]] = (self.tableau[i][-1], -y_k[i])
        # non-basic variables
        for e in self.non_basis:
            if e == enter_axis:
                rc[e] = (0.0, 1.0)
            else:
                rc[e] = (0.0, 0.0)
        rc = dict(sorted(rc.items(), key=lambda x:x[0]))
        return rc

    def _update_tableau(self, enter_axis_idx, leave_axis_idx):
        # update the basis and non-basis
        enter_axis = self.non_basis[enter_axis_idx]
        leave_axis = self.basis[leave_axis_idx]
        self.basis[leave_axis_idx] = enter_axis
        self.non_basis[enter_axis_idx] = leave_axis
        # update the tableau
        self.tableau[leave_axis_idx] = \
            self.tableau[leave_axis_idx] / self.tableau[leave_axis_idx][enter_axis]
        row_num = self.tableau.shape[0]
        col_num = self.tableau.shape[1]
        for row in range(row_num):
            if row == leave_axis_idx:
                continue
            temp_ratio = \
                self.tableau[row][enter_axis] / self.tableau[leave_axis_idx][enter_axis]
            for col in range(col_num):
                self.tableau[row][col] = self.tableau[row][col] - \
                                         temp_ratio * self.tableau[leave_axis_idx][col]

    def _lexicographic_rule(self, y_k):
        assert y_k.size == self.const_num, y_k.size
        ratio = []
        for i in range(self.const_num):
            if y_k[i] > 0 + self._equal_threshold:
                ratio.append(self.tableau[i][-1]/y_k[i])
            else:
                ratio.append(float('inf'))
        ratio = np.array(ratio)
        leave_axis_list = np.where(ratio == np.min(ratio))[0]
        if len(leave_axis_list) > 1:
            col = 0
            while len(leave_axis_list) > 1:
                temp_ratio_list = []
                for r in leave_axis_list:
                    temp_ratio_list.append(self.tableau[r][col]/y_k[r])
                temp_ratio_list = np.array(temp_ratio_list)
                new_leave_axis_list = leave_axis_list[np.where(temp_ratio_list ==
                                                               np.min(temp_ratio_list))[0]]
                leave_axis_list = new_leave_axis_list
                col += 1

        assert len(leave_axis_list) == 1
        return leave_axis_list[0]

    def _categorize_variables(self):

        basic_legitimate_vars, nonbasic_legitimate_vars, basic_artificial_vars, nonbasic_artificial_vars = [], [], [], []
        for var in range(self.var_num):  # all the legitimate variables
            if var in self.basis:
                basic_legitimate_vars.append(var)
            else:
                nonbasic_legitimate_vars.append(var)
        for var in range(self.var_num, self.var_num + self.const_num):  # all the artificial variables
            if var in self.basis:
                basic_artificial_vars.append(var)
            else:
                nonbasic_artificial_vars.append(var)

        return basic_legitimate_vars, nonbasic_legitimate_vars, basic_artificial_vars, nonbasic_artificial_vars

    def _convert_tableau_to_Phase_2(self):

        basic_legitimate_vars, nonbasic_legitimate_vars, basic_artificial_vars, \
        nonbasic_artificial_vars = self._categorize_variables()

        if len(basic_artificial_vars) > 0: # redundancy may exist
            for row in range(self.const_num):
                if not self.basis[row] in basic_artificial_vars:
                    assert self.basis[row] in basic_legitimate_vars
                    continue
                else:
                    # Requirement 3: if the basic artificial variables can't be
                    # pivoted with nonbasic legitimate variables, there is algebraical
                    # redundancy and we will delete that row directly later
                    is_redundancy = True
                    for v in nonbasic_legitimate_vars:
                        #if self.tableau[row][v] != 0:
                        if abs(self.tableau[row][v]) > self._equal_threshold:
                            # pivoting at this non-zero element
                            is_redundancy = False
                            enter_axis_idx = np.where(np.array(self.non_basis) == v)[0][0]
                            self._update_tableau(enter_axis_idx, row)
                            # update the basic artificial variables, etc.
                            basic_legitimate_vars, nonbasic_legitimate_vars, \
                            basic_artificial_vars, nonbasic_artificial_vars =\
                                self._categorize_variables()
                            break
                    if is_redundancy:
                        print("Redundancy occurs at row {} of the tableau!".format(row))

        # create new tableau for Phase 2
        new_tableau = []
        new_basis = []
        for row in range(self.const_num):
            if self.basis[row] < self.var_num:
                new_tableau.append(np.concatenate([self.tableau[row][:self.var_num],
                                                   [self.tableau[row][-1]]]))
                new_basis.append(self.basis[row])
        self.basis = new_basis
        self.const_num = len(new_basis)
        # non_basis
        self.non_basis = []
        for col in range(self.var_num):
            if col not in self.basis:
                self.non_basis.append(col)
        # last row
        last_row = np.zeros((self.var_num + 1, ))
        for col in self.non_basis:
            reduced_cost = -self.C[col] # cost coefficient of the original problem,
            for row in range(self.const_num):
                c_b = self.C[self.basis[row]]
                reduced_cost += c_b * new_tableau[row][col]
            last_row[col] = reduced_cost
        cur_obj = 0.0
        for row in range(self.const_num):
            c_b = self.C[self.basis[row]]
            cur_obj += c_b * new_tableau[row][-1]
        last_row[-1] = cur_obj
        new_tableau.append(last_row)
        self.tableau = np.array(new_tableau).astype(np.float64)

    # main function: linear optimization with two-phase simplex tableau method
    def optimize(self):
        start_time = time.time()
        ## phase 1
        # create initial tableau for phase 1
        print("Phase 1 starts!")
        self._create_init_phase_1_tableau()
        phase_1_result = self._simplex_tableau()
        assert phase_1_result['Type'] == 'optimal'
        # print(phase_1_result)
        # Requirement 1: to detect if the LP at hand is feasible or not
        # if phase_1_result['Optimal Objective'] != 0:
        if abs(phase_1_result['Optimal Objective']) > self._equal_threshold:
            print("The original LP is infeasible!")
        else:
            print("Phase 2 starts!")
            self._convert_tableau_to_Phase_2()
            phase_2_result = self._simplex_tableau()
            # Requirement 6: handle two termination conditions
            if phase_2_result['Type'] == 'optimal':
                print("There is a finite optimal solution for this LP problem!")
                print("Optimal objective: {}.".format(phase_2_result['Optimal Objective']))
                print("The optimal solutions are: ")
                for v in range(len(self.vars_name)):
                    if v in phase_2_result['Optimal Solution'].keys():
                        print("{}: {}".format(self.vars_name[v], \
                                              phase_2_result['Optimal Solution'][v]))
                    else:
                        print("{}: {}".format(self.vars_name[v], 0.0))
            else:
                assert phase_2_result['Type'] == 'unbounded'
                print("The LP problem is unbounded!")
                print("The recession cone for this solution is {}.".format(\
                    phase_2_result['Recession Cone']))

        end_time = time.time()
        print("The total time cost for this task is {}s.".format(end_time - start_time))

# if __name__ == '__main__':
#     ## Model 13
#     vars_name = []
#     for i in range(4):
#         for j in range(4):
#             vars_name.append('x_{}_{}'.format(i+1, j+1))
#     C = [16, 12, 20, 18, 14, 13, 24, 20, 17, 10, 28, 20, 12, 11, 18, 17] # cost coefficient
#     A = [[1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#          [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
#          [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
#          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
#          [17, 0, 0, 0, 15, 0, 0, 0, 13, 0, 0, 0, 10, 0, 0, 0],
#          [0, 14, 0, 0, 0, 16, 0, 0, 0, 12, 0, 0, 0, 11, 0, 0],
#          [0, 0, 10, 0, 0, 0, 12, 0, 0, 0, 14, 0, 0, 0, 8, 0],
#          [0, 0, 0, 9, 0, 0, 0, 11, 0, 0, 0, 8, 0, 0, 0, 6]] # constraints matrix
#     RHS = [1500, 1700, 900, 600, 22.5, 9, 4.8, 3.5] # right hand side of the constraints
#     # the coefficient of the slack variables, related to the constraint type
#     slack_vars = [1, 1, 1, 1, -1, -1, -1, -1]
#     # initialize a LP_model with the above information
#     # note that RHS should be non-negative
#     lp_model = LP_model_solver(vars_name, C, A, RHS, slack_vars, is_min=False)
#     lp_model.optimize()
