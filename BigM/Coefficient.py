import math
import re

class BigMCoefficient:
    def __init__(self, m_coeff: float, const_coeff: float, variable: str = None):
        self.m_coeff = float(m_coeff)
        self.const_coeff = float(const_coeff)
        self.variable = variable
        self.M = 1000.0  # Changed to float

    def __float__(self):
        return float(self.m_coeff * self.M + self.const_coeff)  # Explicitly cast to float

    def __add__(self, other):
        if isinstance(other, BigMCoefficient):
            return BigMCoefficient(self.m_coeff + other.m_coeff, self.const_coeff + other.const_coeff, self.variable or other.variable)
        return BigMCoefficient(self.m_coeff, self.const_coeff + float(other), self.variable)

    def __sub__(self, other):
        if isinstance(other, BigMCoefficient):
            return BigMCoefficient(self.m_coeff - other.m_coeff, self.const_coeff - other.const_coeff, self.variable or other.variable)
        return BigMCoefficient(self.m_coeff, self.const_coeff - float(other), self.variable)

    def __mul__(self, other):
        if isinstance(other, BigMCoefficient):
            return BigMCoefficient(
                self.m_coeff * other.m_coeff + self.m_coeff * other.const_coeff + self.const_coeff * other.m_coeff,
                self.const_coeff * other.const_coeff,
                self.variable or other.variable
            )
        return BigMCoefficient(self.m_coeff * float(other), self.const_coeff * float(other), self.variable)

    def __truediv__(self, other):
        if isinstance(other, BigMCoefficient):
            if other.m_coeff == 0 and other.const_coeff == 0:
                return BigMCoefficient(float('inf'), float('inf'), self.variable)
            elif other.m_coeff == 0:
                return BigMCoefficient(self.m_coeff / other.const_coeff, self.const_coeff / other.const_coeff, self.variable)
            else:
                # This is an approximation and might not be accurate for all cases
                return BigMCoefficient(self.m_coeff / other.m_coeff, self.const_coeff / other.const_coeff, self.variable)
        else:
            other = float(other)
            if other == 0:
                return BigMCoefficient(float('inf'), float('inf'), self.variable)
            return BigMCoefficient(self.m_coeff / other, self.const_coeff / other, self.variable)

    def __neg__(self):
        return BigMCoefficient(-self.m_coeff, -self.const_coeff, self.variable)

    def is_infinite(self):
        return math.isinf(self.m_coeff) or math.isinf(self.const_coeff)

    def __lt__(self, other):
        return float(self) < float(other)

    def __le__(self, other):
        return float(self) <= float(other)

    def __eq__(self, other):
        return float(self) == float(other)

    def __ne__(self, other):
        return float(self) != float(other)

    def __gt__(self, other):
        return float(self) > float(other)

    def __ge__(self, other):
        return float(self) >= float(other)

    def __str__(self):
        if self.m_coeff == 0:
            return f"{self.const_coeff:.2f}"
        elif self.const_coeff == 0:
            return f"{self.m_coeff:.2f}M"
        else:
            sign = "+" if self.const_coeff > 0 else "-"
            return f"{self.m_coeff:.2f}M{sign}{abs(self.const_coeff):.2f}"

    @classmethod
    def from_string(cls, coef_str):
        if isinstance(coef_str, (int, float)):
            return cls(0, float(coef_str))

        # New regex pattern to match complex coefficients
        pattern = r'([-+]?\s*\d*\.?\d*)\s*(M)?\s*(X\d+|S\d+|MS\d+)?(?:([-+]\s*\d*\.?\d*)\s*(X\d+|S\d+|MS\d+)?)?'
        match = re.match(pattern, coef_str.strip())

        if not match:
            raise ValueError(f"Invalid coefficient format: {coef_str}")

        m_coef, m_part, var1, const_coef, var2 = match.groups()

        # Handle the M coefficient part
        if m_coef in ('', '+', '-'):
            m_coef = '1' if m_coef in ('', '+') else '-1'
        m_coeff = float(m_coef) if m_part else 0

        # Handle the constant coefficient part
        if const_coef is None:
            const_coeff = float(m_coef) if not m_part else 0
        else:
            if const_coef in ('', '+', '-'):
                const_coef = '1' if const_coef in ('', '+') else '-1'
            const_coeff = float(const_coef)

        # Determine the variable
        variable = var1 or var2

        return cls(m_coeff, const_coeff, variable)


