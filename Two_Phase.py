import numpy as np
import time
import tkinter as tk

class LP_model_solver(object):
    def __init__(self, vars_name, C, A, RHS, slack_vars, widget, operators, is_min):
        self.vars_name = vars_name
        self.C = np.array(C).astype(np.float64)
        self.A = np.array(A).astype(np.float64)
        self.RHS = np.array(RHS).astype(np.float64)
        self.slack_vars = np.array(slack_vars).astype(np.float64)
        self.original_is_min = is_min  # Guardamos la orientación original del problema
        self.is_min = True  # Siempre trabajamos con minimización internamente
        self._equal_threshold = 1e-6
        self.text_widget = widget
        self.operators = operators
        self._convert_to_standard_form()


    def _convert_to_standard_form(self):
        self.var_num = self.C.size  # total number of variables (before adding slack/surplus)
        self.const_num = self.RHS.size  # total number of constraints
        
        new_A = []
        new_C = list(self.C)

        # For each constraint, add slack or surplus based on the operator
        for i in range(self.const_num):
            if self.operators[i].get() == "≤":
                # Add a slack variable
                slack_col = np.zeros(self.const_num)
                slack_col[i] = 1.0  # Slack variable for the `i-th` constraint
                new_A.append(np.concatenate([self.A[i], slack_col]))  # Append slack to matrix row
                new_C.append(0.0)  # No cost associated with slack variable

            elif self.operators[i].get() == "≥":
                # Add a surplus variable
                surplus_col = np.zeros(self.const_num)
                surplus_col[i] = -1.0  # Surplus variable (negative coefficient)
                new_A.append(np.concatenate([self.A[i], surplus_col]))
                new_C.append(0.0)  # No cost associated with surplus variable

            elif self.operators[i].get() == "=":
                if i < len(self.A):
                    # Add the equality constraint without slack or surplus
                    surplus_col = np.zeros(self.const_num)
                    surplus_col[i] = 0.0  # Surplus variable (negative coefficient)
                    new_A.append(np.concatenate([self.A[i], surplus_col]))
                    new_C.append(0.0)  # No cost associated with surplus variable
                else:
                    print(f"Error: Trying to access index {i} in A which has length {len(self.A)}")

                

        # Update `self.A` and `self.C` with the extended matrix and cost vector
        self.A = np.array(new_A).astype(np.float64)
        self.C = np.array(new_C).astype(np.float64)

        ## convert the original LP to a minimization problem (if not) with standard form
        self.var_num = self.C.size + self.slack_vars.size  # total number of variables
        self.const_num = self.RHS.size # total number of constraints
        # update the cost coefficients
        # Convertimos el problema original a un problema de minimización
        if not self.original_is_min:
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

    def _simplex_tableau(self, text_widget):  # Pass in the text widget
        assert self.const_num == len(self.basis)
        iteration = 0
        
        while any(self.tableau[-1][self.non_basis] > (0 + self._equal_threshold)):
            reduced_cost = self.tableau[-1][self.non_basis]
            
            # Usar la regla de Bland para seleccionar la variable entrante
            positive_indices = [i for i in range(len(reduced_cost)) if reduced_cost[i] > self._equal_threshold]
            if not positive_indices:
                break  # No hay costos reducidos positivos, salir del bucle
            
            enter_axis_idx = np.argmax(reduced_cost)
            enter_axis = self.non_basis[enter_axis_idx]
            y_k = self.tableau[:-1, enter_axis]

            if all(y_k <= (0 + self._equal_threshold)):
                rc = self._get_recession_cone(enter_axis, y_k)
                text_widget.insert(tk.END, "Solution is unbounded\n")
                return {'Type': 'unbounded', 'Recession Cone': rc}
            
            # Usar la regla de Bland para seleccionar la variable saliente
            leave_candidates = [
                (i, self.tableau[i, -1] / y_k[i])
                for i in range(len(y_k))
                if y_k[i] > self._equal_threshold
            ]
        
            if not leave_candidates:
                break  # No hay candidatos para salir, salir del bucle
            
            leave_axis_idx = self._lexicographic_rule(y_k)
            self._update_tableau(enter_axis_idx, leave_axis_idx)  # Perform pivot
            
            # Mostrar tabla con encabezados ordenados
            self._display_tableau(text_widget, iteration)

            cur_sol, cur_obj = self._get_result()
            
            # Display each iteration in the Text widget
            text_widget.insert(tk.END, f"\n=== Iteration #{iteration} ===\n")
            text_widget.insert(tk.END, f"Entering variable: x{enter_axis + 1}\n")
            text_widget.insert(tk.END, f"Leaving variable: x{self.basis[leave_axis_idx] + 1}\n")
            text_widget.insert(tk.END, f"Current objective value: {cur_obj:.4f}\n")
            text_widget.insert(tk.END, "Current basic solution:\n")
            for var, value in cur_sol.items():
                self.text_widget.insert(tk.END, f"x{var + 1}: {value:.4f}\n")
            
            iteration += 1

        optimal_solution, optimal_obj = self._get_result()
        text_widget.insert(tk.END, f"\nOptimal solution found after {iteration} iterations:\n")
        text_widget.insert(tk.END, f"Optimal Objective Value: {optimal_obj:.4f}\n")
        text_widget.insert(tk.END, "Optimal solution (variable: value):\n")
        for var, value in optimal_solution.items():
            text_widget.insert(tk.END, f"x{var + 1}: {value:.4f}\n")
        
        print(self.tableau)

        return {'Type': 'optimal', 'Optimal Solution': optimal_solution, 'Optimal Objective': optimal_obj}


    def _validate_and_correct_z_row(self):
        """ Verifica y corrige si hay valores negativos en la fila Z que deberían ser positivos """
        for i in range(len(self.tableau[-1])):
            if self.tableau[-1][i] < -self._equal_threshold:
                # Corrige el valor para que sea positivo o igual a cero
                self.tableau[-1][i] = abs(self.tableau[-1][i])
    
    def _display_tableau(self, text_widget, iteration):
        # Crear etiquetas dinámicas para las variables de decisión y holgura
        decision_vars = [f"x{i+1}" for i in range(len(self.vars_name))]
        slack_vars = [f"s{i+1}" for i in range(self.const_num)]
        all_vars = decision_vars + slack_vars
        col_labels = all_vars + ["RHS"]

        # Encabezado de las columnas
        text_widget.insert(tk.END, f"\nTabla de Iteración #{iteration}:\n")
        text_widget.insert(tk.END, "  ".join(col_labels) + "\n")

        # Mostrar las filas con las variables básicas
        for row in range(self.const_num):
        # Variable básica (líder)
            lead_var = all_vars[self.basis[row]] if self.basis[row] < len(all_vars) else f"s{self.basis[row] - len(all_vars) + 1}"
            row_values = [f"{v:.2f}" for v in self.tableau[row]]
            text_widget.insert(tk.END, f"{lead_var}  " + "  ".join(row_values) + "\n")

        # Mostrar la última fila (la fila de z)
        z_values = [f"{v:.2f}" for v in self.tableau[-1]]
        text_widget.insert(tk.END, f"z   " + "  ".join(z_values) + "\n")

    def _format_value(self, value):
    # Si el valor es un número entero, muéstralo como entero, de lo contrario, muéstralo con 2 decimales
        if abs(value - round(value)) < self._equal_threshold:  # Compara el valor con su valor redondeado
            return f"{int(round(value))}"  # Mostrar como entero
        else:
            return f"{value:.2f}"  # Mostrar con 2 decimales

    def _get_result(self):
        current_solution = {}
        for row in range(self.const_num):
            current_solution[self.basis[row]] = self.tableau[row][-1]
        current_solution = dict(sorted(current_solution.items(), key=lambda x: x[0]))
        current_obj = self.tableau[-1][-1]
        # Invertimos el signo del objetivo si el problema original era de maximización
        if not self.original_is_min:
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
        print("Inicia Fase 1\n")
        self._create_init_phase_1_tableau()
        phase_1_result = self._simplex_tableau(self.text_widget)
        assert phase_1_result['Type'] == 'optimal'

        if abs(phase_1_result['Optimal Objective']) > self._equal_threshold:
            return {'Type': 'infeasible'}
        else:
            print("Inicia Fase 2\n")
            self._convert_tableau_to_Phase_2()
            phase_2_result = self._simplex_tableau(self.text_widget)

            if phase_2_result['Type'] == 'optimal':
                optimal_obj = phase_2_result['Optimal Objective']
                if not self.original_is_min:
                    optimal_obj *= -1.0  # Invertimos el signo si el problema original era de maximización
                
                return {
                    'Type': 'optimal',
                    'Optimal Solution': {self.vars_name[v]: phase_2_result['Optimal Solution'][v] if v in phase_2_result['Optimal Solution'] else 0.0 for v in range(len(self.vars_name))},
                    'Optimal Objective': optimal_obj
                }
            else:
                print("Unbounded")
                assert phase_2_result['Type'] == 'unbounded'
                return {
                    'Type': 'unbounded',
                    'Recession Cone': phase_2_result['Recession Cone']
                }