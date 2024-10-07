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

    def __rmul__(self, other):
        # This method is called when BigMCoefficient is on the right side of *
        return self.__mul__(other)

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
        if abs(self.m_coeff) < 1e-10 and abs(self.const_coeff) < 1e-10:
            return "0.00"
        elif abs(self.m_coeff) < 1e-10:
            return f"{self.const_coeff:.2f}"
        elif abs(self.const_coeff) < 1e-10:
            return f"{self.m_coeff:.2f}M"
        else:
            sign = "+" if self.const_coeff > 0 else "-"
            return f"{self.m_coeff:.2f}M{sign}{abs(self.const_coeff):.2f}"

    @classmethod
    def from_string(cls, coef_str):
        if isinstance(coef_str, (int, float)):
            return cls(0, float(coef_str))

        if coef_str.strip() == '':
            return cls(0, 0)

        pattern = r'([-+]?\s*\d*\.?\d*)\s*(M)?\s*(X\d+|S\d+|A\d+|MS\d+|MA\d+)?(?:([-+]\s*\d*\.?\d*)\s*(M)?\s*(X\d+|S\d+|A\d+|MS\d+|MA\d+)?)?'
        matches = re.findall(pattern, coef_str.strip())

        m_coeff = 0
        const_coeff = 0
        variable = None

        for match in matches:
            coef, m_part, var1, const_part, const_m_part, var2 = match

            coef = coef.strip()
            if coef == '+':
                coef = '1'
            elif coef == '-':
                coef = '-1'
            elif coef == '':
                coef = '1' if m_part else '0'  # Treat bare 'M' as '1M'
            
            if m_part:
                m_coeff += float(coef)
            else:
                const_coeff += float(coef)

            if const_part:
                const_part = const_part.strip()
                if const_part == '+':
                    const_part = '1'
                elif const_part == '-':
                    const_part = '-1'
                elif const_part == '':
                    const_part = '1' if const_m_part else '0'  # Treat bare 'M' as '1M'
                
                if const_m_part:
                    m_coeff += float(const_part)
                else:
                    const_coeff += float(const_part)

            variable = var1 or var2 or variable

        return cls(m_coeff, const_coeff, variable)

    # @classmethod
    # def from_string(cls, coef_str):
    #     if isinstance(coef_str, (int, float)):
    #         return cls(0, float(coef_str))
    #
    #     if coef_str.strip() == '0' or coef_str.strip() == '':
    #         return cls(0, 0)
    #
    #     pattern = r'([-+]?\s*\d*\.?\d*)\s*(M)?\s*(X\d+|S\d+|A\d+|MS\d+|MA\d+)?(?:([-+]\s*\d*\.?\d*)\s*(M)?\s*(X\d+|S\d+|A\d+|MS\d+|MA\d+)?)?'
    #     matches = re.findall(pattern, coef_str.strip())
    #
    #     m_coeff = 0
    #     const_coeff = 0
    #     variable = None
    #
    #     for match in matches:
    #         coef, m_part, var1, const_part, const_m_part, var2 = match
    #
    #         coef = coef.replace(" ", "")
    #         if coef in ('', '+'):
    #             coef = '0'
    #         elif coef == '-':
    #             coef = '0'
    #        
    #         if m_part:
    #             m_coeff += float(coef)
    #         else:
    #             const_coeff += float(coef)
    #
    #         if const_part:
    #             const_part = const_part.replace(" ", "")
    #             if const_part in ('', '+'):
    #                 const_part = '0'
    #             elif const_part == '-':
    #                 const_part = '0'
    #            
    #             if const_m_part:
    #                 m_coeff += float(const_part)
    #             else:
    #                 const_coeff += float(const_part)
    #
    #         variable = var1 or var2 or variable
    #
    #     return cls(m_coeff, const_coeff, variable)

