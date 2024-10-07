import re
import sys
from collections import defaultdict

class BigMPreprocessor:
    def __init__(self, coef, constr, op_constr, res_constr, minimize=True):
        self.coef = coef
        self.constr = constr
        self.op_constr = op_constr
        self.res_constr = res_constr
        self.minimize = minimize
        self.num_vars = len(coef)
        self.num_constraints = len(constr)

        self.M = 1000  # Big M value
        self.slack_count = 1
        self.artificial_count = 1
        self.artificial_vars = []
        self.objective = ""
        self.constraints = []

    def _add_variables(self):
        for i in range(self.num_constraints):
            constraint = ""
            for j in range(self.num_vars):
                constraint += f"{self.constr[i][j]}X{j+1} + "

            if self.op_constr[i] == '<=':
                constraint += f"S{self.slack_count} = {'+' if self.res_constr[i] >= 0 else '-' } {self.res_constr[i]}"
                self.slack_count += 1
            elif self.op_constr[i] == '>=':
                constraint += f"-S{self.slack_count} + A{self.artificial_count} = {'+' if self.res_constr[i] >= 0 else '-' } {self.res_constr[i]}"
                self.artificial_vars.append(f"A{self.artificial_count}")
                self.slack_count += 1
                self.artificial_count += 1
            else:  # '='
                constraint += f"A{self.artificial_count} = {'+' if self.res_constr[i] >= 0 else '-' } {self.res_constr[i]}"
                self.artificial_vars.append(f"A{self.artificial_count}")
                self.artificial_count += 1

            self.constraints.append(constraint)

    def _construct_objective(self):
        self.objective = "Z - "
        for i, c in enumerate(self.coef):
            self.objective += f"{c}X{i+1} - "

        self.objective = self.objective.rstrip(" -")

        m_term = "-" if self.minimize else "+"
        for var in self.artificial_vars:
            self.objective += f" {m_term} M{var}"

    def _eliminate_artificial_vars(self):
        def split_polynomial(expression):
            # Find all terms and their signs
            terms = re.findall(r'([+-]?)\s*([\d.]*[A-Z]?\d*)', expression)
            
            # Initialize lists for the terms and signs
            terms_list = []
            signs_list = []
            
            for sign, term in terms:
                # If no sign is given, assume it's positive
                sign = sign if sign else '+'
                
                if term:
                    # Separate the coefficient and the literal
                    match = re.match(r'(\d*\.?\d*)([A-Z]?\d*)', term)
                    if match:
                        coefficient = match.group(1)
                        literal = match.group(2)
                        
                        # Add the "M" literal
                        if coefficient:
                            modified_term = f"{coefficient}M{literal}"
                        else:
                            modified_term = f"M{literal}"
                        
                        terms_list.append(modified_term)
                        signs_list.append(sign)
            
            return terms_list, signs_list

        def clear_parenthesis(terms, signs, minimize):
            e = ""

            # Check the same lenght in both lists
            if len(terms) != len(signs):
                print("Error clearing parenthesis: signs and terms do not coincide")
                sys.exit()

            # Instead of add into the function the constraint as -/+ ( ... ) clear the parenthesis already
            for i in range(len(terms) - 1):
                if minimize:
                    e += f" {'+' if signs[i] == '+' else '-'} {terms[i]}"
                else:
                    e += f" {'-' if signs[i] == '+' else '+'} {terms[i]}"

            e += f" {signs[-1]} {terms[-1]}"

            return e

        for i, constraint in enumerate(self.constraints):
            if any(var in constraint for var in self.artificial_vars):
                terms, signs = split_polynomial(constraint)
                new_constraint = clear_parenthesis(terms, signs, self.minimize)
                self.objective += new_constraint

        self.objective += " = 0"


    def simplify_objective(self):
        # Split the objective function into left and right sides
        left_side, right_side = self.objective.replace(" ", "").split('=')
        
        # Process the left side
        terms = re.findall(r'([+-]?(?:\d*\.?\d*)?M?[A-Z]?\d*)', left_side)
        simplified_terms = defaultdict(float)


        for term in terms:
            # Extract coefficient and variable
            match = re.match(r'([+-]?(?:\d*\.?\d*)?)(M?)([A-Z]?\d*)', term)
            if match:
                coef, m, var = match.groups()

                # Process coefficient
                if coef in ('', '+'):
                    coef = 1.0
                elif coef == '-':
                    coef = -1.0
                else:
                    coef = float(coef) if coef else 0.0  # Set to 0.0 if coef is empty
                
                # Combine M with variable
                full_var = (m + var) if m else var
                
                # Only add to simplified terms if there's a non-zero coefficient
                if full_var and (coef != 0.0 or full_var == 'Z'):
                    if full_var == 'Z':
                        simplified_terms[full_var] = 1.0  # Z always has a coefficient of 1
                    else:
                        simplified_terms[full_var] += coef
        
        # Reconstruct the simplified objective function
        simplified_obj = "Z"
        m_term = 0
        
        # Group terms
        x_terms = []
        mx_terms = []
        ma_terms = []
        ms_terms = []
        
        for var, coef in simplified_terms.items():
            if abs(coef) > 1e-10:  # Avoid very small coefficients due to float precision
                if var.startswith('X'):
                    x_terms.append(f"{' + ' if coef > 0 else ' - '}{abs(coef):.1f}{var}")
                elif var.startswith('MS'):
                    ms_terms.append(f"{' + ' if coef > 0 else ' - '}{abs(coef):.1f}{var}")
                elif var.startswith('MX'):
                    mx_terms.append(f"{' + ' if coef > 0 else ' - '}{abs(coef):.1f}{var}")
                elif var.startswith('MA'):
                    ma_terms.append(f"{' + ' if coef > 0 else ' - '}{abs(coef):.1f}{var}")
                elif var == 'M':
                    m_term += coef
                elif var != 'Z':
                    m_term += coef

        # Combine all terms
        simplified_obj += ''.join(x_terms + mx_terms + ma_terms + ms_terms)
        
        # Construct the right side of the equation
        if abs(m_term) > 1e-10:
            right_side = f"{-m_term:.1f}M" if not self.minimize else f"{m_term:.1f}M"
        else:
            right_side = "0"
        
        self.objective = f"{simplified_obj} = {right_side}"

    def preprocess(self):
        self._add_variables()
        self._construct_objective()
        self._eliminate_artificial_vars()
        self.simplify_objective()

        return self.objective, self.constraints

    def get_slack_var_count(self):
        return self.slack_count - 1

    def get_artificial_vars(self):
        return self.artificial_vars

if __name__ == "__main__":

    # coef = [3.0, 5.0]
    # constr = [[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]]
    # op_constr = ['<=', '<=', '=']
    # res_constr = [4.0, 12.0, 18.0]
    # minimize = False
    
    # coef = [0.4, 0.5]
    # constr = [[0.3, 0.1], [0.5, 0.5], [0.6, 0.4]]
    # op_constr = ['<=', '=', '>=']
    # res_constr = [2.7, 6.0, 6.0]
    # minimize = True

    coef = [3.0, 2.0]
    constr = [[2.0, 1.0], [2.0, 3.0]]
    op_constr = ['>=', '>=']
    res_constr = [18.0, 42.0]
    minimize = True

    preprocessor = BigMPreprocessor(coef, constr, op_constr, res_constr, minimize)
    objective, constraints = preprocessor.preprocess()

    print("Objective function:")
    print(objective)
    print("\nConstraints:")
    print(constraints)

    print(f"\nNumber of slack variables: {preprocessor.get_slack_var_count()}")
    print(f"Artificial variables: {preprocessor.get_artificial_vars()}")

