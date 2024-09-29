import tkinter as tk
from tkinter import messagebox

class SimplexSolver:
    def __init__(self, n, m, c, A, b):
        self.n = n  # Number of variables
        self.m = m  # Number of constraints
        self.c = c  # Objective function coefficients
        self.A = A  # Coefficients matrix for constraints
        self.b = b  # Right-hand side values for constraints

    def pivot(self, tabla, row, col):
        pivot_element = tabla[row][col]
        tabla[row] = [x / pivot_element for x in tabla[row]]

        for i in range(len(tabla)):
            if i != row:
                ratio = tabla[i][col]
                tabla[i] = [tabla[i][j] - ratio * tabla[row][j] for j in range(len(tabla[i]))]

    def simplex(self, text_widget):
        iteracion = 1
        n, m, c, A, b = self.n, self.m, self.c, self.A, self.b
        
        # Initialize table
        tabla = [[0] * (n + m + 1) for _ in range(m + 1)]
        for i in range(m):
            tabla[i][:n] = A[i]
            tabla[i][n + i] = 1
            tabla[i][-1] = b[i]

        tabla[-1][:n] = [-ci for ci in c]

        self.imprimir_tabla(tabla, text_widget, iteracion)
        iteracion += 1

        while any(tabla[-1][j] < 0 for j in range(n + m)):
            col = min(range(n + m), key=lambda j: tabla[-1][j])

            ratios = []
            for i in range(m):
                if tabla[i][col] > 0:
                    ratios.append((tabla[i][-1] / tabla[i][col], i))
                else:
                    ratios.append((float('inf'), i))
            row = min(ratios)[1]

            if ratios[row][0] == float('inf'):
                raise ValueError("Problema no acotado, no hay solución óptima.")

            text_widget.insert(tk.END, f"Pivote en fila {row+1}, columna {col+1}\n")
            self.pivot(tabla, row, col)
            self.imprimir_tabla(tabla, text_widget, iteracion)
            iteracion += 1

        solucion = [0] * n
        for i in range(n):
            columna = [tabla[j][i] for j in range(m)]
            if columna.count(1) == 1 and columna.count(0) == m - 1:
                fila = columna.index(1)
                solucion[i] = tabla[fila][-1]

        valor_optimo = tabla[-1][-1]

        text_widget.insert(tk.END, "Solución óptima:\n")
        for i in range(n):
            text_widget.insert(tk.END, f"x{i+1} = {solucion[i]:.4f}\n")
        text_widget.insert(tk.END, f"Valor óptimo de la función objetivo: {valor_optimo:.4f}\n")

    def imprimir_tabla(self, tabla, text_widget, iteracion):
        text_widget.insert(tk.END, f"Tabla Simplex - Iteración {iteracion}:\n")
        for fila in tabla:
            text_widget.insert(tk.END, "\t".join(map("{:.2f}".format, fila)) + "\n")
        text_widget.insert(tk.END, "\n")

