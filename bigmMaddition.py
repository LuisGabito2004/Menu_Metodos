from typing import List, Tuple
import re

def big_m_addition(objective: str, constraints: List[str]) -> str:
    # Parse the objective function
    obj_terms = parse_equation(standardize_objective_function(objective))
    # Parse and negate the constraint equations
    neg_constraints = [negate_equation(parse_equation(eq)) for eq in constraints]
    
    # Combine all terms
    all_terms = obj_terms + [term for eq in neg_constraints for term in eq]
    
    # Consolidate like terms
    consolidated = consolidate_terms(all_terms)

    # Format the result
    result = destandardize_objective_function(format_equation(consolidated))
    
    return result

def standardize_objective_function(equation: str) -> str:
    # Remove spaces and split the equation into left and right sides
    equation = equation.replace(" ", "")
    left, right = equation.split("=")
    
    # Ensure the left side is just 'Z'
    if left != "Z":
        raise ValueError("The left side of the equation must be 'Z'")
    
    # Split the right side into terms
    terms = right.replace("-", "+-").split("+")
    
    # Process each term
    standardized_terms = []
    for term in terms:
        if term:
            if term[0] == "-":
                standardized_terms.append("+" + term[1:])
            else:
                standardized_terms.append("-" + term)
    
    # Combine the terms and add the left side
    standardized_equation = "Z " + " ".join(standardized_terms) + " = 0"
    
    return standardized_equation

def destandardize_objective_function(equation: str) -> str:
    # Remove spaces and split the equation into left and right sides
    equation = equation.replace(" ", "")
    left, right = equation.split("=")
    
    # Ensure the left side starts with 'Z'
    if not left.startswith("Z"):
        raise ValueError("The left side of the equation must start with 'Z'")
    
    # Split the left side into terms (excluding 'Z')
    terms = left[1:].replace("-", "+-").split("+")
    
    # Process each term
    destandardized_terms = []
    for term in terms:
        if term:
            if term[0] == "-":
                destandardized_terms.append("+" + term[1:])
            else:
                destandardized_terms.append("-" + term)
    
    # Combine the terms and add the left side
    destandardized_equation = "Z = " + " ".join(destandardized_terms)[1:] + right  # Remove the leading '+'
    
    return destandardized_equation

def parse_equation(eq: str) -> List[Tuple[float, str]]:
    eq = eq.replace(" ", "").replace("=", " ").replace("+", " +").replace("-", " -").split()

    terms = []
    for term in eq:
        if 'M' in term and 'S' in term:
            coef, var = term.split('M')
            coef = float(coef) if coef and coef not in ['+', '-'] else float(coef + '1')
            var = 'M' + var
        elif'M' in term and 'X' in term:
            coef, var = term.split('M')
            coef = float(coef) if coef and coef not in ['+', '-'] else float(coef + '1')
            var = 'M' + var
        elif 'X' in term or 'S' in term:
            coef, var = term.split('X' if 'X' in term else 'S')
            var = ('X' if 'X' in term else 'S') + var
            coef = float(coef) if coef and coef not in ['+', '-'] else float(coef + '1')
        elif 'M' in term:
            coef, var = 1.0, 'M'
            if term != 'M':
                coef = float(term.replace('M', ''))
        elif 'Z' in term:
            coef, var = 1.0, 'Z'
        else:
            coef, var = float(term), '='

        terms.append((coef, var))

    return terms

def negate_equation(eq: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
    if not any('M' in var for _, var in eq):
        return ()
        
    return [(-coef, ('M' + var) if 'M' not in var else var) for coef, var in eq]

def consolidate_terms(terms: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
    consolidated = {}
    for coef, var in terms:
        consolidated[var] = consolidated.get(var, 0) + coef
    return [(coef, var) for var, coef in consolidated.items() if coef != 0]

def format_equation(terms: List[Tuple[float, str]]) -> str:
    formatted = []

    for coef, var in sorted(terms, key=lambda x: (x[1] != 'Z', '=' in x[1], x[1])):
        formatted.append('=') if '=' in var else var
        var = var.replace("=", "") if '=' in var else var

        if coef == 0:
            continue
        if coef == 1 and var:
            term = f"+{var}"
        elif coef == -1 and var:
            term = f"-{var}"
        elif coef > 0:
            term = f"+{coef}{var}"
        else:
            term = f"{coef}{var}"
        formatted.append(term)
    
    result = " ".join(formatted).strip("+")
    return result if result else "0"

if __name__ == "__main__":
    # Example usage
    objective = "Z = 3X1 + 5X2 - MS3"
    # objective = "Z = 3X1 + 5X2 - MS3"
    constraints = [
        "3X1 + 2X2 + MS3 = 18",
    ]

    result = big_m_addition(objective, constraints)
    print(result)

    # FORMATO CANONICO
    # X1 ≤ 4
    # 2X2 ≤ 12
    # 3X1 + 2X2 = 18

    # FORMATO LIBRE
    # X1 + S1 = 4
    # 2X2 + S2 = 12
    # 3X1 + 2X2 + MS3 = 18

    # FUNCION OBJETIVO
    # Z = 3X1 + 5X2             -- Antes
    # Z = 3X1 + 5X2 - MS3       -- Despues

    # Z - 3X1 - 5X2 + MS3= 0
    # −3MX1−2MX2−MS3=−18M
    # ------------------------------------
    # Z-(3M+3)X1 – (2M+5)X2 = -18M

    # Z -3.0MX1 -2.0MX2 -3.0X1 -5.0X2 = -18.0M
    # Z= -18M + (3M + 3)X1 + (2M + 5)X2
