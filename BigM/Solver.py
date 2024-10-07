from typing import List, Tuple
from sys import exit
# from PolynomialAddition import big_m_addition
# from Coefficient import BigMCoefficient
# from Preprocessor import BigMPreprocessor
from BigM.PolynomialAddition import big_m_addition
from BigM.Coefficient import BigMCoefficient
from BigM.Preprocessor import BigMPreprocessor
import numpy as np
import re
import tkinter as tk
import math

class BigMSolver:
    def __init__(
            self,
            num_var: int,
            num_constr: int,
            coefs_objective: List[str],
            coefs_constr: List[List[float]],
            op_constr,
            res_constr: List[float],
            is_min: bool = False
        ):
        self.num_var = num_var
        self.num_restr = num_constr
        self.coef_objective = coefs_objective
        self.coef_restr = coefs_constr
        self.op_constr = op_constr
        self.res_restr = res_constr
        self.is_min = is_min
        
        self.all_variables = []

        Preprocessor = BigMPreprocessor(coefs_objective, coefs_constr, op_constr, res_constr, is_min)
        objective, constraints = Preprocessor.preprocess()
        self.list_tableau = self.parse_problem(objective, constraints)

        self.M = 1000  # A large number to represent M
        self.slack_vars = sum(1 for op in op_constr if op in ['<=', '>='])
        self.artificial_vars = sum(1 for op in op_constr if op in ['=', '>='])
        
        self.tableau = self.create_initial_tableau()

    def create_initial_tableau(self):
        rows = len(self.list_tableau)
        cols = len(self.list_tableau[-1])
        tableau = [[BigMCoefficient(0, 0) for _ in range(cols)] for _ in range(rows)]
    
        for i in range(len(self.list_tableau)):
            for j in range(len(self.list_tableau[i])):
                if i == rows - 1:  # This is the objective row
                    if self.is_min:
                        # For minimization, we negate the objective coefficients
                        coeff = BigMCoefficient.from_string(self.list_tableau[i][j])
                        tableau[i][j] = BigMCoefficient(-coeff.m_coeff, coeff.const_coeff, coeff.variable)
                    else:
                        # For maximization, we use the coefficients as they are
                        tableau[i][j] = BigMCoefficient.from_string(self.list_tableau[i][j])
                else:
                    # For constraint rows, we use the coefficients as they are
                    tableau[i][j] = BigMCoefficient.from_string(self.list_tableau[i][j])
    
        return tableau

    def solve(self, text_widget):
        iteration = 0
        while True:
            self.print_tableau(text_widget, iteration)
            # self._print_tableau_DEBUG(text_widget, iteration)
    
            # Find the pivot column
            pivot_col = min(range(len(self.tableau[0]) - 1), key=lambda j: float(self.tableau[-1][j]))
            if float(self.tableau[-1][pivot_col]) >= -1e-10:  # Use a small tolerance for floating-point comparisons
                break  # Optimal solution reached
    
            # Find the pivot row
            ratios = []
            for i in range(len(self.tableau) - 1):
                if float(self.tableau[i][pivot_col]) <= 0:
                    ratios.append(BigMCoefficient(float('inf'), float('inf')))
                else:
                    ratios.append(self.tableau[i][-1] / self.tableau[i][pivot_col])
    
            if all(ratio.is_infinite() for ratio in ratios):
                print("The problem is unbounded.\n")
                text_widget.insert(tk.END, "The problem is unbounded.\n")
                return None, None
    
            pivot_row = min(range(len(ratios)), key=lambda i: float(ratios[i]))
    
            # Perform pivot operation
            pivot_element = self.tableau[pivot_row][pivot_col]
            self.tableau[pivot_row] = [elem / pivot_element for elem in self.tableau[pivot_row]]
            for i in range(len(self.tableau)):
                if i != pivot_row:
                    self.tableau[i] = [self.tableau[i][j] - self.tableau[i][pivot_col] * self.tableau[pivot_row][j]
                                       for j in range(len(self.tableau[i]))]
    
            iteration += 1
    
        # Print final tableau
        self.print_tableau(text_widget, iteration, is_final=True)
        # self._print_tableau_DEBUG(text_widget, iteration, is_final=True)
    
        # Extract and return the solution
        solution = [0] * self.num_var
        for i in range(self.num_var):
            col = [self.tableau[j][i] for j in range(len(self.tableau) - 1)]
            if sum(1 for elem in col if float(elem) != 0) == 1:
                row = next(j for j, elem in enumerate(col) if float(elem) != 0)
                solution[i] = float(self.tableau[row][-1])
    
        objective_value = float(self.tableau[-1][-1])
        if self.is_min:
            objective_value = -objective_value  # Negate for minimization problems
    
        return solution, objective_value

    def print_tableau(self, text_widget, iteration, is_final=False):
        text_widget.insert(tk.END, f"{'Final ' if is_final else ''}Tableau - Iteration {iteration}:\n")
        
        # Use all_variables for headers, adding 'RHS' at the end
        headers = self.all_variables + ['RHS']
        text_widget.insert(tk.END, "\t".join(headers) + "\n")

        for row in self.tableau:
            text_widget.insert(tk.END, "\t".join(str(coeff) for coeff in row) + "\n")
        text_widget.insert(tk.END, "\n")

    def _print_tableau_DEBUG(self, text_widget, iteration, is_final=False):
        print(f"{'Final ' if is_final else ''}Tableau - Iteration {iteration}:\n")
        
        # Use all_variables for headers, adding 'RHS' at the end
        headers = self.all_variables + ['RHS']
        print("\t".join(headers) + "\n")

        for row in self.tableau:
            print("\t".join(str(coeff) for coeff in row) + "\n")
        print("\n")

    def parse_problem(self, objective: str, constraints: List[str]):
        def parse_terms(expression):
            return re.findall(r'([+-]?\s*\d*\.?\d*)\s*(MX\d+|X\d+|MS\d+|S\d+|MA\d+|A\d+|M)', expression)

        def parse_coef(coef):
            coef = coef.strip().replace(' ', '')
            if coef in ('+', '-'):
                return 1.0 if coef == '+' else -1.0
            elif coef == '':
                return 1.0
            else:
                return float(coef)

        def eliminate_empty_cols(matrix):
            transposed = list(map(list, zip(*matrix)))
            filtered = [row for row in transposed if any(value not in {0, None, '0'} for value in row)]
            result = list(map(list, zip(*filtered)))
            return result

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
        x_terms = []
        a_terms = []
        s_terms = []

        for _, var in obj_terms:
            if var not in ['M', 'MX', 'MS', 'MA']:
                if var.startswith('X') and var not in x_terms:
                    x_terms.append(var)
                elif var.startswith('S') and var not in s_terms:
                    s_terms.append(var)
                elif var.startswith('A') and var not in a_terms:
                    a_terms.append(var)
        for constraint in constraints:
            constr_terms = parse_terms(constraint.split('=')[0])
            for _, var in constr_terms:
                if var not in ['M', 'MX', 'MS', 'MA']:
                    if var.startswith('X') and var not in x_terms:
                        x_terms.append(var)
                    elif var.startswith('S') and var not in s_terms:
                        s_terms.append(var)
                    elif var.startswith('A') and var not in a_terms:
                        a_terms.append(var)

        self.all_variables = x_terms + s_terms + a_terms
        num_var = len(self.all_variables)
        var_to_index = {x: i for i, x in enumerate(self.all_variables)}

        # Parse objective function
        coefs_objective = ['0.0'] * num_var
        for coef, var in obj_terms:
            coef = coef.replace(" ", "")
            if var == 'M':
                coefs_objective.append(coef + 'M')
            elif var.startswith('MX') or var.startswith('MS') or var.startswith('MA'):
                index = var_to_index.get(var[1:], len(coefs_objective))
                if index == len(coefs_objective):
                    coefs_objective.append(coef + var)
                else:
                    if '0.0' in coefs_objective[index]:
                        coefs_objective[index] = coef + var
                    else:
                        coefs_objective[index] += coef + var
            elif var in var_to_index:
                if '0.0' in coefs_objective[var_to_index[var]]:
                    coefs_objective[var_to_index[var]] = coef + var
                else:
                    coefs_objective[var_to_index[var]] += coef + var
            else:
                coefs_objective.append(coef + var)

        coefs_objective = [v if not '0.0' in v else '0' for v in coefs_objective]

        # Parse constraints
        matrix = []
        coefs_constr = []  # Add objective function as the first row

        for constraint in constraints:
            left, right = constraint.split('=')
            constr_terms = parse_terms(left)
            constr_coefs = ['0'] * len(coefs_objective)
            
            for coef, var in constr_terms:
                if var in var_to_index:
                    constr_coefs[var_to_index[var]] = coef.replace(" ", "") + var.replace(" ", "")
                elif var.startswith('MX') or var.startswith('MS') or var.startswith('MA'):
                    index = next((i for i, v in enumerate(coefs_objective) if v.endswith(var)), None)
                    if index is not None:
                        constr_coefs[index] = coef.replace(" ", "") + var.replace(" ", "")
                    else:
                        constr_coefs.append(coef.replace(" ", "") + var.replace(" ", ""))
                else:
                    constr_coefs.append(coef.replace(" ", "") + var.replace(" ", ""))
            
            constr_coefs[-1] = right.strip().replace(" ", "")
            coefs_constr.append(constr_coefs)
            
        coefs_constr.append(coefs_objective)

        return coefs_constr

# PARSED
# [4.0, 2.0]
# [[5.0, 1.0], [4.0, 3.0]]
# [10.0, 36.0]

# FORMATO CANONICO
# Z = 3X1 + 5X2  
# X1 + 0X2 ≤ 4
# 0X1 + 2X2 ≤ 12
# 3X1 + 2X2 = 18

if __name__ == "__main__":
    var_num = 2
    constr_num = 3

    # coef = [0.4, 0.5]
    # constr = [[0.3, 0.1], [0.5, 0.5], [0.6, 0.4]]
    # op_constr = ['<=', '=', '>=']
    # res_constr = [2.7, 6.0, 6.0]
    # minimize = True

    # coef = [3.0, 5.0]
    # constr = [[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]]
    # op_constr = ['<=', '<=', '=']
    # res_constr = [4.0, 12.0, 18.0]
    # minimize = False
    #
    constr_num = 2
    coef = [3.0, 2.0]
    constr = [[2.0, 1.0], [2.0, 3.0]]
    op_constr = ['>=', '>=']
    res_constr = [18.0, 42.0]
    minimize = True

    obj = BigMSolver(var_num, constr_num, coef, constr, op_constr, res_constr, minimize)
    obj.solve(None)


