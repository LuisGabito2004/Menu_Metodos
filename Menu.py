import tkinter as tk
from tkinter import messagebox
import Simplex
import Two_Phase
from Two_Phase import LP_model_solver
from BigM.Solver import BigMSolver
from tabulate import tabulate

class SimplexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Métodos de Programación Lineal")
        self.root.configure(bg="#f0f0f0")  # Fondo claro para la ventana
        self.operators = []

        # Variables para los inputs del Simplex
        self.entry_vars = {
            "n": tk.StringVar(),
            "m": tk.StringVar(),
            "c": []  # Cambiamos a una lista para manejar múltiples entradas de coeficientes
        }
        self.restricciones_entries = []
        self.method = tk.StringVar(value="Simplex")  # Método predeterminado
        self.opt_type = tk.StringVar(value="Maximizar")  # Variable para el tipo de optimización (Maximizar/Minimizar)

        # Mostrar la primera vista de selección de método
        self.show_method_selector()

    def show_method_selector(self):
        """Muestra el selector de método con botones azules"""
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(pady=20, padx=10)

        tk.Label(frame, text="Seleccione el método a utilizar:", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        # Botones de selección de método
        button_frame = tk.Frame(frame, bg="#f0f0f0")
        button_frame.pack()

        self.simplex_button = tk.Button(button_frame, text="Método Simplex", font=("Arial", 12), bg="#2196F3", fg="white", width=20, command=lambda: self.select_method("Simplex"))
        self.simplex_button.pack(side=tk.LEFT, padx=5)

        self.big_m_button = tk.Button(button_frame, text="Método Gran M", font=("Arial", 12), bg="#2196F3", fg="white", width=20, command=lambda: self.select_method("Big M"))
        self.big_m_button.pack(side=tk.LEFT, padx=5)

        self.two_phase_button = tk.Button(button_frame, text="Método de Dos Fases", font=("Arial", 12), bg="#2196F3", fg="white", width=20, command=lambda: self.select_method("Two Phase"))
        self.two_phase_button.pack(side=tk.LEFT, padx=5)

        # Botón para continuar
        tk.Button(frame, text="Continuar", command=self.create_widgets, font=("Arial", 12, "bold"), bg="#4caf50", fg="white", width=25).pack(pady=20)

    def select_method(self, method):
        """Actualiza el método seleccionado y cambia el color de los botones"""
        self.method.set(method)

        # Restablecer el color de los botones a azul
        self.simplex_button.config(bg="#2196F3")
        self.big_m_button.config(bg="#2196F3")
        self.two_phase_button.config(bg="#2196F3")

        # Cambiar el color del botón seleccionado a azul fuerte
        if method == "Simplex":
            self.simplex_button.config(bg="#0013ff")
        elif method == "Big M":
            self.big_m_button.config(bg="#0013ff")
        elif method == "Two Phase":
            self.two_phase_button.config(bg="#0013ff")

    def create_widgets(self):
        """Crea los campos de entrada según el método seleccionado"""
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(pady=20, padx=10)

        # Mostrar el método seleccionado y permitir cambiarlo
        tk.Label(frame, text="Cambiar método:", font=("Arial", 14), bg="#f0f0f0").grid(row=0, column=0, columnspan=3)

        self.simplex_button = tk.Button(frame, text="Método Simplex", font=("Arial", 12), bg="#2196F3", fg="white", width=20, command=lambda: self.select_method("Simplex"))
        self.simplex_button.grid(row=1, column=0, padx=5, pady=5)

        self.big_m_button = tk.Button(frame, text="Método Gran M", font=("Arial", 12), bg="#2196F3", fg="white", width=20, command=lambda: self.select_method("Big M"))
        self.big_m_button.grid(row=1, column=1, padx=5, pady=5)

        self.two_phase_button = tk.Button(frame, text="Método de Dos Fases", font=("Arial", 12), bg="#2196F3", fg="white", width=20, command=lambda: self.select_method("Two Phase"))
        self.two_phase_button.grid(row=1, column=2, padx=5, pady=5)

        # Menú desplegable para seleccionar Maximizar o Minimizar
        tk.Label(frame, text="Tipo de optimización:", font=("Arial", 12), bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=10)
        opt_menu = tk.OptionMenu(frame, self.opt_type, "Maximizar", "Minimizar")
        opt_menu.config(font=("Arial", 12))
        opt_menu.grid(row=2, column=1, padx=10, pady=1)

        # Mostrar los campos de entrada
        tk.Label(frame, text="Número de variables:", font=("Arial", 12), bg="#f0f0f0").grid(row=3, column=0, sticky="e", padx=10, pady=1)
        tk.Entry(frame, textvariable=self.entry_vars["n"], font=("Arial", 12), width=10).grid(row=3, column=1, padx=10)

        tk.Label(frame, text="Número de restricciones:", font=("Arial", 12), bg="#f0f0f0").grid(row=4, column=0, sticky="e", padx=10, pady=1)
        tk.Entry(frame, textvariable=self.entry_vars["m"], font=("Arial", 12), width=10).grid(row=4, column=1, padx=10)

        # Botón para generar campos de la función y las restricciones
        tk.Button(frame, text="Generar campos de las coeficientes", command=self.crear_campos_restricciones, font=("Arial", 12, "bold"), bg="#4caf50", fg="white", width=30).grid(row=5, column=0, columnspan=2, pady=10)

        # Widget de texto para mostrar resultados
        self.text_widget = tk.Text(self.root, height=15, width=70, font=("Arial", 12))
        self.text_widget.pack(pady=10)

        # Botón para resolver
        tk.Button(self.root, text="Resolver", command=self.resolver, font=("Arial", 12, "bold"), bg="#4caf50", fg="white", width=20).pack(pady=10)

        self.constraints_frame = frame

    def generar_coeficientes(self):
        """Genera campos de entrada para los coeficientes de la función objetivo según el número de variables"""
        for widget in self.coef_widgets:
            widget.destroy()
        self.coef_widgets.clear()

        try:
            n = int(self.entry_vars["n"].get())
            for j in range(n):
                coef_var = tk.StringVar()
                self.entry_vars["c"].append(coef_var)
                entry = tk.Entry(self.constraints_frame, textvariable=coef_var, font=("Arial", 12), width=5)
                entry.grid(row=4, column=j + 1, padx=5)
                self.coef_widgets.append(entry)
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese un número válido de variables.")
    
    def crear_campos_restricciones(self):
        """Genera dinámicamente los campos de las restricciones y coeficientes de la función objetivo"""
        for widget in self.constraints_frame.winfo_children():
            widget.destroy()

        self.restricciones_entries.clear()
        self.entry_vars["c"] = []  # Reiniciar los coeficientes de la función objetivo

        try:
            m = int(self.entry_vars["m"].get())
            n = int(self.entry_vars["n"].get())

            # Menú desplegable para seleccionar Maximizar o Minimizar, colocado en el centro
            tk.Label(self.constraints_frame, text="Tipo de optimización:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=10)
            opt_menu = tk.OptionMenu(self.constraints_frame, self.opt_type, "Maximizar", "Minimizar")
            opt_menu.config(font=("Arial", 12))
            opt_menu.grid(row=0, column=1, columnspan=n, padx=5, pady=1, sticky="ew")  # Ajuste del menú al centro

            # Crear campos para los coeficientes de la función objetivo
            tk.Label(self.constraints_frame, text="Función Objetivo:", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=10)
            self.coef_widgets = []
            for j in range(n):
                coef_var = tk.StringVar()
                self.entry_vars["c"].append(coef_var)
                # Colocar la etiqueta "Xj" después de cada entrada
                entry = tk.Entry(self.constraints_frame, textvariable=coef_var, font=("Arial", 12), width=5)
                entry.grid(row=1, column=j * 2 + 1, padx=(2 if j > 0 else 2), pady=2)  # Espaciado uniforme
                self.coef_widgets.append(entry)
                tk.Label(self.constraints_frame, text=f"X{j+1}", font=("Arial", 8), bg="#f0f0f0").grid(row=1, column=j * 2 + 2, padx=2)  # Luego la etiqueta

            for i in range(m):
                restriccion_var_b = tk.StringVar()
                self.restricciones_entries.append({"b": restriccion_var_b, "A": []})

                # Crear campos para los coeficientes de la restricción
                tk.Label(self.constraints_frame, text=f"Restricción {i+1}:", font=("Arial", 12), bg="#f0f0f0").grid(row=i + 2, column=0, sticky="e", padx=10, pady=1)

                for j in range(n):
                    coef_var = tk.StringVar()
                    self.restricciones_entries[i]["A"].append(coef_var)
                    # Colocar la etiqueta "Xj" después de cada entrada
                    entry = tk.Entry(self.constraints_frame, textvariable=coef_var, font=("Arial", 12), width=5)
                    entry.grid(row=i + 2, column=j * 2 + 1, padx=(2 if j > 0 else 2), pady=2)  # Espaciado uniforme
                    tk.Label(self.constraints_frame, text=f"X{j+1}", font=("Arial", 8), bg="#f0f0f0").grid(row=i + 2, column=j * 2 + 2, padx=2)  # Luego la etiqueta

                # Menú desplegable para operadores (≤, ≥, =)
                operator_var = tk.StringVar(self.constraints_frame)
                method = self.method.get()

                # Obtener el método seleccionado
                method = self.method.get()

                # Crear una variable para almacenar el valor seleccionado del operador
                operator_var = tk.StringVar(self.constraints_frame)

                if method == "Simplex":
                    operator_var.set("≤")  # Valor por defecto
                    operator_menu = tk.OptionMenu(self.constraints_frame, operator_var, "≤", "≥")
                elif method == "Big M" or method == "Two Phase":
                    operator_var.set("≤")  # Valor por defecto
                    operator_menu = tk.OptionMenu(self.constraints_frame, operator_var, "≤", "≥", "=")

                # Configurar y colocar el menú de selección del operador
                operator_menu.config(font=("Arial", 12), bg="#f0f0f0")
                operator_menu.grid(row=i + 2, column=n * 2 + 1, sticky="e", padx=10)
                self.operators.append(operator_var)

                # Campo para el término independiente de la restricción
                tk.Entry(self.constraints_frame, textvariable=restriccion_var_b, font=("Arial", 12), width=10).grid(row=i + 2, column=n * 2 + 2, padx=10)

            # Añadir la condición de no negatividad
            tk.Label(self.constraints_frame, text="X1, X2, Xk ≥ 0", font=("Arial", 12), bg="#f0f0f0").grid(row=m + 2, column=0, columnspan=n + 3, sticky="w", padx=10, pady=10)

            # Botón para regresar a la vista anterior (create_widgets)
            tk.Button(self.constraints_frame, text="Regresar", command=self.create_widgets, font=("Arial", 12), bg="#767676", fg="white", width=20).grid(row=m + 3, column=0, columnspan=3, pady=10)

        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores válidos.")
            self.create_widgets()

    def display_results(result):
        print("Resultados de la optimización:")
        print("Tipo de solución:", result['Type'])
        if result['Type'] == 'optimal':
            print("Objetivo óptimo:", result['Optimal Objective'])
            print("Solución óptima:")
            for var, value in result['Optimal Solution'].items():
                print(f"Variable {var}: {value}")
        elif result['Type'] == 'unbounded':
            print("El problema es ilimitado.")
            print("Cono de recesión:", result['Recession Cone'])


    def resolver(self):
        """Resuelve el problema con el método seleccionado"""
        self.text_widget.delete(1.0, tk.END)

        try:
            n = int(self.entry_vars["n"].get())
            m = int(self.entry_vars["m"].get())
            c = [float(var.get()) for var in self.entry_vars["c"]]  # Obtener coeficientes de la lista
            
            if len(c) != n:
                messagebox.showerror("Error", f"Se esperaban {n} coeficientes para la función objetivo.")
                return

            A = [list(map(float, (entry["A"][j].get() for j in range(n)))) for entry in self.restricciones_entries]
            b = [float(entry["b"].get()) for entry in self.restricciones_entries]

            if len(A) != m or any(len(row) != n for row in A):
                messagebox.showerror("Error", f"Se esperaban {m} restricciones, cada una con {n} coeficientes.")
                return
            if len(b) != m:
                messagebox.showerror("Error", f"Se esperaban {m} valores en el lado derecho de las restricciones.")
                return

            method = self.method.get()

            if method == "Simplex":
                self.text_widget.insert(tk.END, "Resolviendo con Método Simplex...\n")
                solver = Simplex.SimplexSolver(n, m, c, A, b)
                solver.simplex(self.text_widget)
            elif method == "Big M":
                self.text_widget.insert(tk.END, "Resolviendo con Método M...\n")
                o = [self.operators[i].get().replace('≤', '<=').replace('≥', '>=') for i in range(m)]
                solver = BigMSolver(n, m, c, A, o, b)
                solver.solve(self.text_widget)
            elif method == "Two Phase":
                self.text_widget.insert(tk.END, "Resolviendo con Método de Dos Fases...\n")

                if self.opt_type.get() == "Maximizar":
                    is_min = False
                else:
                    is_min = True
                
                if is_min == True:
                    is_min = self.opt_type.get() == "Minimizar"
                # Crear los nombres de las variables según el número de variables
                vars_name = [f"x{i+1}" for i in range(n)]
                
                # Asume que los coeficientes de las variables holgura (slack_vars) son 1 y tamaño m
                slack_vars = [1 for _ in range(m)]

                # Crear el objeto del solucionador de dos fases
                #solver = Two_Phase.LP_model_solver(vars_name, c, A, b, slack_vars, widget=self.text_widget, operators=self.operators ,is_min=True)
                solver = Two_Phase.LP_model_solver(vars_name, c, A, b, slack_vars, operators=self.operators, widget=self.text_widget, is_min = is_min)

                # Llamar al método para resolver en dos fases
                result = solver.optimize()

                # Mostrar el resultado en el text_widget
                if result['Type'] == 'optimal':
                    self.text_widget.insert(tk.END, "Solución óptima encontrada:\n")
                    self.text_widget.insert(tk.END, f"Valor óptimo: {result['Optimal Objective']}\n")
                    self.text_widget.insert(tk.END, "Soluciones óptimas:\n")
                    for var, value in result['Optimal Solution'].items():
                        self.text_widget.insert(tk.END, f"Variable {var}: {value}\n")
                elif result['Type'] == 'unbounded':
                    self.text_widget.insert(tk.END, "El problema es ilimitado.\n")
                    self.text_widget.insert(tk.END, f"Cono de recesión: {result['Recession Cone']}\n")
            else:
                self.text_widget.insert(tk.END, "El problema no tiene solución factible.\n")

        except ValueError as ve:
            messagebox.showerror("Error", f"Por favor ingrese valores válidos: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error: {e}")

# Ejecutar la aplicación de Tkinter
if __name__ == "__main__":
    root = tk.Tk()
    app = SimplexApp(root)
    root.mainloop()