import tkinter as tk
from tkinter import messagebox
import Simplex
import Two_Phase
from Two_Phase import LP_model_solver

class SimplexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Métodos de Programación Lineal")
        self.root.configure(bg="#f0f0f0")  # Fondo claro para la ventana

        # Variables para los inputs del Simplex
        self.entry_vars = {
            "n": tk.StringVar(),
            "m": tk.StringVar(),
            "c": []  # Cambiamos a una lista para manejar múltiples entradas de coeficientes
        }
        self.restricciones_entries = []
        self.method = tk.StringVar(value="Simplex")  # Método predeterminado

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

        # Mostrar los campos de entrada
        tk.Label(frame, text="Número de variables:", font=("Arial", 12), bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=10)
        tk.Entry(frame, textvariable=self.entry_vars["n"], font=("Arial", 12), width=10).grid(row=2, column=1, padx=10)

        tk.Label(frame, text="Número de restricciones:", font=("Arial", 12), bg="#f0f0f0").grid(row=3, column=0, sticky="e", padx=10)
        tk.Entry(frame, textvariable=self.entry_vars["m"], font=("Arial", 12), width=10).grid(row=3, column=1, padx=10)

        # Botón para generar campos de la función y las restricciones
        tk.Button(frame, text="Generar campos de las coeficientes", command=self.crear_campos_restricciones, font=("Arial", 12, "bold"), bg="#4caf50", fg="white", width=30).grid(row=4, column=0, columnspan=2, pady=10)

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

            # Crear campos para los coeficientes de la función objetivo
            tk.Label(self.constraints_frame, text="Función Objetivo:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=10)
            self.coef_widgets = []
            for j in range(n):
                coef_var = tk.StringVar()
                self.entry_vars["c"].append(coef_var)
                entry = tk.Entry(self.constraints_frame, textvariable=coef_var, font=("Arial", 12), width=5)
                entry.grid(row=0, column=j + 1, padx=5)
                self.coef_widgets.append(entry)

            for i in range(m):
                restriccion_var_b = tk.StringVar()
                self.restricciones_entries.append({"b": restriccion_var_b, "A": []})

                # Crear campos para los coeficientes de la restricción
                tk.Label(self.constraints_frame, text=f"Restricción {i+1}:", font=("Arial", 12), bg="#f0f0f0").grid(row=i + 1, column=0, sticky="e", padx=10)

                for j in range(n):
                    coef_var = tk.StringVar()
                    self.restricciones_entries[i]["A"].append(coef_var)
                    tk.Entry(self.constraints_frame, textvariable=coef_var, font=("Arial", 12), width=5).grid(row=i + 1, column=j + 1, padx=5)

                # Etiqueta para el lado derecho de la restricción
                # Crear una variable para almacenar el valor seleccionado
                self.operator_var = tk.StringVar(self.constraints_frame)
                self.operator_var.set("≤")  # Valor por defecto

                # Crear el OptionMenu
                operator_menu = tk.OptionMenu(self.constraints_frame, self.operator_var, "≤", "≥", "=")
                operator_menu.config(font=("Arial", 12), bg="#f0f0f0")

                # Colocar el OptionMenu en la posición deseada
                operator_menu.grid(row=i + 1, column=n + 1, sticky="e", padx=10)

                tk.Entry(self.constraints_frame, textvariable=restriccion_var_b, font=("Arial", 12), width=10).grid(row=i + 1, column=n + 2, padx=10)

            # Añadir la condición de no negatividad
            tk.Label(self.constraints_frame, text="X1, X2 ≥ 0", font=("Arial", 12), bg="#f0f0f0").grid(row=m + 1, column=0, columnspan=n + 3, sticky="w", padx=10, pady=10)

        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores válidos.")
            self.create_widgets()

    def get_input():
        # Solicitar nombres de variables
        vars_name = input("Ingrese los nombres de las variables (separados por comas): ").split(',')
        vars_name = [name.strip() for name in vars_name]
        
        # Solicitar coeficientes de costo
        C = list(map(float, input("Ingrese los coeficientes de costo (separados por comas): ").split(',')))
        
        # Solicitar matriz de restricciones
        A = []
        num_constraints = int(input("Ingrese el número de restricciones: "))
        for i in range(num_constraints):
            row = list(map(float, input(f"Ingrese los coeficientes de la restricción {i+1} (separados por comas): ").split(',')))
            A.append(row)

        # Solicitar RHS
        RHS = list(map(float, input("Ingrese los valores del lado derecho de las restricciones (separados por comas): ").split(',')))
        
        # Solicitar valores de las variables de holgura
        slack_vars = list(map(float, input("Ingrese los coeficientes de las variables de holgura (separados por comas): ").split(',')))

        # Devolver los datos obtenidos
        return vars_name, C, A, RHS, slack_vars

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

    def main(self):
        print("Bienvenido al solucionador de problemas de programación lineal.")
        vars_name, C, A, RHS, slack_vars = self.get_input()
        
        # Inicializar el modelo de LP
        lp_model = LP_model_solver(vars_name, C, A, RHS, slack_vars, is_min=False)
        result = lp_model.optimize()

        # Mostrar resultado
        self.display_results(result)

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
                solver = Simplex.BigMSolver(n, m, c, A, b)
                solver.solve_with_big_m(self.text_widget)
            elif method == "Two Phase":
                self.text_widget.insert(tk.END, "Resolviendo con Método de Dos Fases...\n")
                
                # Crear el objeto de TwoPhaseSolver (que está en el archivo Two Phase.py)
                solver = Two_Phase.LP_model_solver(n, c, A, b, [0]*n, is_min=False)
                
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
            else:
                messagebox.showerror("Error", "Método no soportado.")
        except ValueError as ve:
            messagebox.showerror("Error", f"Por favor ingrese valores válidos: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error: {e}")

# Ejecutar la aplicación de Tkinter
if __name__ == "__main__":
    root = tk.Tk()
    app = SimplexApp(root)
    root.mainloop()
    app.main()
