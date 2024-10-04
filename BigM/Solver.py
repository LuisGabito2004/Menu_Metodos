from typing import List, Tuple
from sys import exit
#from PolynomialAddition import big_m_addition
#from Coefficient import BigMCoefficient
from BigM.PolynomialAddition import big_m_addition
from BigM.Coefficient import BigMCoefficient
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

        print("===============================")
        coef_str, constr_str = self.generate_str()
        print(coef_str, constr_str)
        new_coef, new_constrs = self.canonical2standard(coef_str, constr_str)
        print(new_coef, new_constrs)
        result = big_m_addition(new_coef, new_constrs)
        print("PolynomialAdditionL: ", result)
        self.coef_objective, self.coef_restr = self.parse_problem(result, new_constrs)
        print("Objetive: ", self.coef_objective)
        print("Constriants: ", self.coef_restr)
        print("ResultConstraints: ", self.res_restr)
        print("===============================")

        self.M = 1000  # A large number to represent M
        self.slack_vars = sum(1 for op in op_constr if op in ['<=', '>='])
        self.artificial_vars = sum(1 for op in op_constr if op in ['=', '>='])
        
        self.tableau = self.create_initial_tableau()

    def create_initial_tableau(self):
        rows = self.num_restr + 1
        cols = len(self.coef_objective)
        tableau = [[BigMCoefficient(0, 0) for _ in range(cols)] for _ in range(rows)]
    
        # Set constraint coefficients
        for i in range(self.num_restr):
            for j in range(len(self.coef_restr[i])):
                tableau[i][j] = self.parse_coefficient(self.coef_restr[i][j])
            # Set the RHS of constraints
            tableau[i][-1] = BigMCoefficient(0, self.res_restr[i])
    
        # Set objective function coefficients
        for j in range(len(self.coef_objective)):
            coef = self.parse_coefficient(self.coef_objective[j])
            if self.is_min:
                tableau[-1][j] = -coef  # Negate coefficients for minimization
            else:
                tableau[-1][j] = coef
    
        # Set the RHS of the objective row
        tableau[-1][-1] = self.parse_coefficient(self.coef_objective[-1])
    
        return tableau
    
    def parse_coefficient(self, coef_str: str) -> BigMCoefficient:
        return BigMCoefficient.from_string(coef_str)

    def solve(self, text_widget):
        iteration = 0
        while True:
            self.print_tableau(text_widget, iteration)
            self._print_tableau_DEBUG(text_widget, iteration)
    
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
        self._print_tableau_DEBUG(text_widget, iteration, is_final=True)
    
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
        headers = [f"x{i+1}" for i in range(self.num_var)] + \
                  [f"s{i+1}" for i in range(self.slack_vars + self.artificial_vars)] + ["RHS"]
        text_widget.insert(tk.END, "\t".join(headers) + "\n")

        for row in self.tableau:
            text_widget.insert(tk.END, "\t".join(str(coeff) for coeff in row) + "\n")
        text_widget.insert(tk.END, "\n")

    def _print_tableau_DEBUG(self, text_widget, iteration, is_final=False):
        print(f"{'Final ' if is_final else ''}Tableau - Iteration {iteration}:\n")
        headers = [f"x{i+1}" for i in range(self.num_var)] + \
                  [f"s{i+1}" for i in range(self.slack_vars + self.artificial_vars)] + ["RHS"]
        print("\t".join(headers) + "\n")

        for row in self.tableau:
            print("\t".join(str(coeff) for coeff in row) + "\n")

    def generate_str(self) -> Tuple[str, List[str]]:
        if not self.is_min:
            objective = "Z = "
            for i in range(self.num_var):
                coef = self.coef_objective[i]
                if float(coef) >= 0 and i != 0:
                    objective += f"+ {coef}X{i+1} "
                else:
                    objective += f"{coef}X{i+1} "
        else:
            objective = "Z = -("
            for i in range(self.num_var):
                coef = self.coef_objective[i]
                if float(coef) >= 0 and i != 0:
                    objective += f"+ {coef}X{i+1} "
                else:
                    objective += f"{coef}X{i+1} "
            objective += ")"
    
        constraints = []
        for i in range(self.num_restr):
            constraint = ""
            for j in range(self.num_var):
                coef = self.coef_restr[i][j]
                if float(coef) >= 0 and j != 0:
                    constraint += f"+ {coef}X{j+1} "
                else:
                    constraint += f"{coef}X{j+1} "
            # Append the right-hand side
            constraint += f"{self.op_constr[i]} {self.res_restr[i]}"
            constraints.append(constraint)
    
        return objective, constraints

    def canonical2standard(self, coef: str, constrs: List[str]) -> Tuple[str, List[str]]:
        new_constrs = []
        added_vars = []
        s_count = 0  # Counter for slack and surplus variables
        ms_count = 0  # Counter for artificial variables
    
        for constr in constrs:
            s_count += 1
            if '>=' in constr:
                # For >= constraints, subtract a surplus variable and add an artificial variable
                ms_count += 1
                tmp = f'- S{s_count} + MS{ms_count} = '
                new_constr = constr.replace('>=', tmp)
                added_vars.append(f'MS{ms_count}')
            elif '<=' in constr:
                # For <= constraints, add a slack variable
                new_constr = constr.replace('<=', f'+ S{s_count} = ')
            elif '=' in constr:
                # For equality constraints, add an artificial variable
                ms_count += 1
                new_constr = constr.replace('=', f'+ MS{ms_count} = ')
                added_vars.append(f'MS{ms_count}')
            else:
                new_constr = constr  # No change if no recognized operator
            new_constrs.append(new_constr)
    
        # Process objective function
        if self.is_min:
            coef = coef.replace("Z = -(", "Z = ").replace(")", "")
        if added_vars:
            # Add negative M variables (use a large M value, e.g., 1000)
            coef += ' - ' + ' - '.join(added_vars)
    
        return coef, new_constrs

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
        all_variables = []
        for _, var in obj_terms:
            if var not in all_variables and var not in ['M', 'MX']:
                all_variables.append(var)
        for constraint in constraints:
            constr_terms = parse_terms(constraint.split('=')[0])
            for _, var in constr_terms:
                if var not in all_variables and var != 'M':
                    all_variables.append(var)
    
        num_var = len(all_variables)
        var_to_index = {x: i for i, x in enumerate(all_variables)}
    
        # Parse objective function
        coefs_objective = ['0.0'] * num_var
        for coef, var in obj_terms:
            if var == 'M':
                coefs_objective.append(coef + 'M')
            elif var.startswith('MX') or var.startswith('MS'):
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
                coefs_objective[var_to_index[var]] = '0'
        coefs_objective = [v if not '0.0' in v else '0' for v in coefs_objective ]
    
        # Parse constraints
        coefs_constr = [coefs_objective]  # Add objective function as the first row
    
        for constraint in constraints:
            left, right = constraint.split('=')
            constr_terms = parse_terms(left)
            constr_coefs = ['0'] * len(coefs_objective)
            
            for coef, var in constr_terms:
                if var in var_to_index:
                    constr_coefs[var_to_index[var]] = coef.replace(" ", "") + var.replace(" ", "")
            
                
            constr_coefs[-1] = right.strip()
            coefs_constr.append(constr_coefs)
            
            matrix = eliminate_empty_cols(coefs_constr)
    
        return matrix[0], matrix[1::]

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

    coef = [0.4, 0.5]
    constr = [[0.3, 0.1], [0.5, 0.5], [0.6, 0.4]]
    op_constr = ['<=', '=', '>=']
    res_constr = [2.7, 6.0, 6.0]

    #coef = [3.0, 5.0]
    #constr = [[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]]
    #op_constr = ['<=', '<=', '=']
    #res_constr = [4.0, 12.0, 18.0]

    obj = BigMSolver(var_num, constr_num, coef, constr, op_constr, res_constr, True)

    obj.solve(None)

