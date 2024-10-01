from typing import List, Tuple
from bigmMaddition import big_m_addition
import numpy as np
import re
import tkinter as tk
from tkinter import messagebox

class BigMSolver:
    def __init__(
            self,
            num_var: int, #variable names
            num_constr: int, #restrictions count
            coefs_objective: List[float], #objetive funcion
            coefs_constr: List[List[float]], #coefficient list
            op_constr,
            res_constr: List[float], #restriction results
            is_min: bool = False # minimize
        ):
        self.num_var = num_var
        self.num_restr = num_constr
        self.coef_objective = coefs_objective
        self.coef_restr = coefs_constr
        self.op_constr = op_constr
        self.res_restr = res_constr
        self.is_min = is_min

        coef_str, constr_str = self.generate_str()
        new_coef, new_constrs = self.canonical2standard(coef_str, constr_str)
        result = big_m_addition(new_coef, new_constrs)
        self.coef_objective, self.coef_restr, self.res_restr = self.parse_problem(result, new_constrs)

        self.M = 1000  # A large number to represent M
        self.slack_vars = sum(1 for op in op_constr if op in ['<=', '>='])
        self.artificial_vars = sum(1 for op in op_constr if op in ['=', '>='])
        self.total_vars = num_var + self.slack_vars + self.artificial_vars

        self.tableau = self.create_initial_tableau()

    def create_initial_tableau(self):
        rows = self.num_restr + 1
        cols = self.total_vars + 1  # +1 for RHS

        tableau = np.zeros((rows, cols))

        # Set objective function coefficients
        for i in range(self.num_var):
            tableau[0, i] = -self.coef_objective[i]

        # Set constraint coefficients and RHS
        for i in range(self.num_restr):
            for j in range(self.num_var):
                tableau[i+1, j] = self.coef_restr[i][j]
            tableau[i+1, -1] = self.res_restr[i]

        # Add slack and artificial variables
        slack_art_col = self.num_var
        for i in range(self.num_restr):
            if self.op_constr[i] == '<=':
                tableau[i+1, slack_art_col] = 1
                slack_art_col += 1
            elif self.op_constr[i] == '>=':
                tableau[i+1, slack_art_col] = -1
                slack_art_col += 1
                tableau[i+1, slack_art_col] = 1
                tableau[0, slack_art_col] = -self.M
                slack_art_col += 1
            elif self.op_constr[i] == '=':
                tableau[i+1, slack_art_col] = 1
                tableau[0, slack_art_col] = -self.M
                slack_art_col += 1

        return tableau

    def solve(self, text_widget):
        iteration = 0
        while True:
            self.print_tableau(text_widget, iteration)

            # Find the pivot column
            pivot_col = np.argmin(self.tableau[0, :-1])
            if self.tableau[0, pivot_col] >= 0:
                break  # Optimal solution reached

            # Find the pivot row
            ratios = self.tableau[1:, -1] / self.tableau[1:, pivot_col]
            pivot_row = np.argmin(ratios[ratios > 0]) + 1

            # Perform pivot operation
            pivot_element = self.tableau[pivot_row, pivot_col]
            self.tableau[pivot_row] /= pivot_element
            for i in range(len(self.tableau)):
                if i != pivot_row:
                    self.tableau[i] -= self.tableau[i, pivot_col] * self.tableau[pivot_row]

            iteration += 1

        # Print final tableau
        self.print_tableau(text_widget, iteration, is_final=True)

        # Extract and return the solution
        solution = [0] * self.num_var
        for i in range(self.num_var):
            col = self.tableau[:, i]
            if np.count_nonzero(col) == 1:
                row = np.nonzero(col)[0][0]
                if row != 0:
                    solution[i] = self.tableau[row, -1]

        objective_value = -self.tableau[0, -1] if not self.is_min else self.tableau[0, -1]
        return solution, objective_value

    def print_tableau(self, text_widget, iteration, is_final=False):
        text_widget.insert(tk.END, f"{'Final ' if is_final else ''}Tableau - Iteration {iteration}:\n")
        headers = [f"x{i+1}" for i in range(self.num_var)] + \
                  [f"s{i+1}" for i in range(self.slack_vars)] + \
                  [f"a{i+1}" for i in range(self.artificial_vars)] + ["RHS"]
        text_widget.insert(tk.END, "\t".join(headers) + "\n")

        for row in self.tableau:
            text_widget.insert(tk.END, "\t".join(f"{x:.2f}" for x in row) + "\n")
        text_widget.insert(tk.END, "\n")


    def transform_big_m_objective(self, expression: str) -> List[str]:
        # Step 1: Separate the X terms
        terms = re.findall(r'([+-]?\s*\d*\.?\d*M?X?\d*)', expression)
        grouped_terms = {}
        term_order = []
        
        for term in terms:
            if 'X' in term:
                x_num = re.search(r'X(\d*)', term).group(1)
                x_num = x_num if x_num else '1'
                if x_num not in grouped_terms:
                    grouped_terms[x_num] = []
                    term_order.append(x_num)
                grouped_terms[x_num].append(term.strip())
            elif 'M' in term and 'X' not in term:
                if 'M' not in grouped_terms:
                    grouped_terms['M'] = []
                    term_order.append('M')
                grouped_terms['M'].append(term.strip())
        
        # Step 2: Eliminate similar X and join terms
        result_step2 = []
        for key in term_order:
            group = grouped_terms[key]
            if group:
                m_sum = sum(float(re.search(r'([+-]?\s*\d*\.?\d*)M', term).group(1) or '1') for term in group if 'M' in term)
                non_m_sum = sum(float(re.search(r'([+-]?\s*\d*\.?\d*)', term).group(1) or '1') for term in group if 'M' not in term)
                
                if 'X' in group[0]:
                    result = f"{m_sum}M{'+' if non_m_sum >= 0 else ''}{non_m_sum}"
                else:
                    result = f"{m_sum}M"
                
                result_step2.append(result)
        
        return result_step2

    def generate_str(self) -> Tuple[str, List[str]]:
        objective = "Z="
        for i in range(self.num_var):
            coef = self.coef_objective[i]
            if coef >= 0 and i != 0:
                objective += f"+ {coef}X{i+1} "
            else:
                objective += f" {coef}X{i+1} "
                
        constraints = []
        for i in range(self.num_restr):
            constraint = ""
            for j in range(self.num_var):
                coef = self.coef_restr[i][j]
                if coef >= 0 and j != 0:
                    constraint += f"+ {coef}X{j+1} "
                else:
                    constraint += f"{coef}X{j+1} "
            # Append the right-hand side
            constraint += f"{self.op_constr[i]} {self.res_restr[i]}"
            constraints.append(constraint)

        # Combine the objective and constraints into standard form
        return objective, constraints

    def canonical2standard(self, coef: str, constrs: List[str]) -> Tuple[str, List[str]]:
        # Process constraints
        new_constrs = []
        added_vars = []
        for i, constr in enumerate(constrs):
            if '>=' in constr:
                new_constr = constr.replace('>=', f'- S{i+1} = ')
            elif '<=' in constr:
                new_constr = constr.replace('<=', f'+ S{i+1} = ')
            elif '=' in constr:
                new_constr = constr.replace('=', f'+ MS{i+1} = ')
                added_vars.append(f'MS{i+1}')
            else:
                new_constr = constr  # No change if no recognized operator
            new_constrs.append(new_constr)
        
        # Process objective function
        if added_vars:
            # Split the objective function into left and right parts
            left, right = coef.split('=')
            # Add negative M variables
            right += ' '.join(f'- {var}' for var in added_vars)
            new_coef = f"{left.strip()} = {right.strip()}"
        else:
            new_coef = coef
        
        return new_coef, new_constrs
                
    def parse_problem(self, objective: str, constraints: List[str]) -> Tuple[List[str], List[List[float]], List[float]]:
        def parse_terms(expression):
            return re.findall(r'([+-]?\s*\d*\.?\d*)\s*(MX\d+|X\d+|MS\d+|S\d+|M)', expression)

        def parse_coef(coef):
            coef = coef.strip().replace(' ', '')
            if coef in ('+', '-'):
                return 1.0 if coef == '+' else -1.0
            elif coef == '':
                return 1.0
            else:
                return float(coef)

        # Parse objective function
        obj_match = re.match(r'Z\s*=\s*(.*)', objective)
        if not obj_match:
            obj_match = re.match(r'Z\s*(.*)\s*=\s*(.*)', objective)
            if obj_match:
                objective = f"Z = {obj_match.group(1)}{obj_match.group(2)}"
            else:
                raise ValueError("Invalid objective function format")

        obj_terms = parse_terms(objective)

        # Collect all variables from objective and constraints
        all_variables = []
        for _, var in obj_terms:
            if var not in all_variables and var not in ['M', 'MX1', 'MX2']:
                all_variables.append(var)
        for constraint in constraints:
            constr_terms = parse_terms(constraint.split('=')[0])
            for _, var in constr_terms:
                if var not in all_variables:
                    all_variables.append(var)

        num_var = len(all_variables)
        var_to_index = {x: i for i, x in enumerate(all_variables)}

        # Parse objective function
        coefs_objective = [0.0] * num_var
        m_coef = 0.0
        for coef, var in obj_terms:
            coef = parse_coef(coef)
            if var == 'M':
                m_coef = coef
            elif var.startswith('MX'):
                x_var = 'X' + var[2:]
                if x_var in var_to_index:
                    coefs_objective[var_to_index[x_var]] -= coef * m_coef
            elif var in var_to_index:
                coefs_objective[var_to_index[var]] += coef

        # Parse constraints
        coefs_constr = []
        res_constr = []
        
        for constraint in constraints:
            left, right = constraint.split('=')
            constr_terms = parse_terms(left)
            constr_coefs = [0.0] * num_var
            
            for coef, var in constr_terms:
                coef = parse_coef(coef)
                if var in var_to_index:
                    constr_coefs[var_to_index[var]] += coef
        
            coefs_constr.append(constr_coefs)
            res_constr.append(float(right.strip()))
        
        return self.transform_big_m_objective(objective), coefs_constr, res_constr

# PARSED
# [4.0, 2.0]
# [[5.0, 1.0], [4.0, 3.0]]
# [10.0, 36.0]

# FORMATO CANONICO
# Z = 3X1 + 5X2  
# X1 ≤ 4
# 2X2 ≤ 12
# 3X1 + 2X2 = 18

if __name__ == "__main__":
    var_num = 2
    constr_num = 3
    coef = [3.0, 5.0]
    constr = [[1.0, 1.0], [2.0, 1.0], [3.0, 2.0]]
    op_constr = ['<=', '<=', '=']
    res_constr = [4.0, 12.0, 18.0]
    obj = BigMSolver(var_num, constr_num, coef, constr, op_constr, res_constr)

    coef, constrs = obj.generate_str()
    new_coef, new_constrs = obj.canonical2standard(coef, constrs)
    result = big_m_addition(new_coef, new_constrs)
    objective, constraints, results_constraints = obj.parse_problem(result, new_constrs)


# I am creating a big M method solver my breakpoints are:
# 1. Get the inputs, i end up with this
#     var_num = 2
#     constr_num = 3
#     coef = [3.0, 5.0]
#     constr = [[1.0, 1.0], [2.0, 1.0], [3.0, 2.0]]
#     op_constr = ['<=', '<=', '=']
#     res_constr = [4.0, 12.0, 18.0]
# 2. Instance the bigmclass and convert it to a more readable string, separating the objective and constraints
#     'Z= 3.0X1 + 5.0X2'
#     ['1.0X1 + 1.0X2 <= 4.0', '2.0X1 + 1.0X2 <= 12.0', '3.0X1 + 2.0X2 = 18.0']
# 3. transform from canonical to standart
#     'Z = 3.0X1 + 5.0X2 - MS3'
#     ['1.0X1 + 1.0X2 + S1 =  4.0', '2.0X1 + 1.0X2 + S2 =  12.0', '3.0X1 + 2.0X2 + MS3 =  18.0']
# 4. Make the main Polynomial addition to create the new objective function
#     '−3MX1−2MX2−MS3=−18M'
# 5. Parsed again the entire result to end with the structure i beggined with
#     ['3.0M+3.0', '2.0M+5.0', '-18.0M']
#     [[1.0, 1.0, 1.0, 0.0, 0.0], [2.0, 1.0, 0.0, 1.0, 0.0], [3.0, 2.0, 0.0, 0.0, 1.0]]
#     [4.0, 12.0, 18.0]
# this is how i would like to print the table to show the user the progress with tkinter
# def print_tabla(self, tabla, text_widget, iteracion):
#     text_widget.insert(tk.END, f"Tabla Simplex - Iteración {iteracion}:\n")
#     for fila in tabla:
#         text_widget.insert(tk.END, "\t".join(map("{:.2f}".format, fila)) + "\n")
#     text_widget.insert(tk.END, "\n")
# implement the solver function andhif needed the adjustment on `print_tabla`, i attach the class i have,
# the constructur have the breakpoints i talked to you