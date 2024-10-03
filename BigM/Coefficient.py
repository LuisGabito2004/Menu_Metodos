import math

class BigMCoefficient:
    def __init__(self, m_coeff: float, const_coeff: float):
        self.m_coeff = float(m_coeff)
        self.const_coeff = float(const_coeff)
        self.M = 1000.0  # Changed to float

    def __float__(self):
        return float(self.m_coeff * self.M + self.const_coeff)  # Explicitly cast to float

    def __add__(self, other):
        if isinstance(other, BigMCoefficient):
            return BigMCoefficient(self.m_coeff + other.m_coeff, self.const_coeff + other.const_coeff)
        return BigMCoefficient(self.m_coeff, self.const_coeff + float(other))

    def __sub__(self, other):
        if isinstance(other, BigMCoefficient):
            return BigMCoefficient(self.m_coeff - other.m_coeff, self.const_coeff - other.const_coeff)
        return BigMCoefficient(self.m_coeff, self.const_coeff - float(other))

    def __mul__(self, other):
        if isinstance(other, BigMCoefficient):
            return BigMCoefficient(
                self.m_coeff * other.m_coeff + self.m_coeff * other.const_coeff + self.const_coeff * other.m_coeff,
                self.const_coeff * other.const_coeff
            )
        return BigMCoefficient(self.m_coeff * float(other), self.const_coeff * float(other))

    def __truediv__(self, other):
        if isinstance(other, BigMCoefficient):
            if other.m_coeff == 0 and other.const_coeff == 0:
                return BigMCoefficient(float('inf'), float('inf'))
            elif other.m_coeff == 0:
                return BigMCoefficient(self.m_coeff / other.const_coeff, self.const_coeff / other.const_coeff)
            else:
                # This is an approximation and might not be accurate for all cases
                return BigMCoefficient(self.m_coeff / other.m_coeff, self.const_coeff / other.const_coeff)
        else:
            other = float(other)
            if other == 0:
                return BigMCoefficient(float('inf'), float('inf'))
            return BigMCoefficient(self.m_coeff / other, self.const_coeff / other)

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
            return f"{self.m_coeff}M"
        else:
            sign = "+" if self.const_coeff > 0 else "-"
            return f"{self.m_coeff}M{sign}{abs(self.const_coeff):.2f}"

    @classmethod
    def from_string(cls, coef_str):
        if isinstance(coef_str, (int, float)):
            return cls(0, float(coef_str))

        parts = coef_str.split('M')
        if len(parts) > 1:
            m_coef = float(parts[0]) if parts[0] else 1
            const_part = parts[1].strip('+')
            const_coef = float(const_part) if const_part else 0
        else:
            m_coef = 0
            const_coef = float(coef_str)

        return cls(m_coef, const_coef)

