import tkinter as tk
from tkinter import messagebox
import Simplex

class SimplexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Métodos de Programación Lineal")
        self.frame = ""
        # Variables for simplex inputs
        self.entry_vars = {
            "n": tk.StringVar(),
            "m": tk.StringVar(),
            "c": tk.StringVar()
        }
        self.restricciones_entries = []
        self.method = tk.StringVar(value="Simplex")  # Default method is Simplex
        
        # Show method selector first
        self.show_method_selector()

    def show_method_selector(self):
        """Displays a method selection menu"""
        frame = tk.Frame(self.root)
        frame.pack(pady=10, padx=10)

        tk.Label(frame, text="Seleccione el método a utilizar:").pack()

        tk.Radiobutton(frame, text="Método Simplex", variable=self.method, value="Simplex", command=self.update_method_view).pack(anchor="w")
        tk.Radiobutton(frame, text="Método Gran M", variable=self.method, value="Big M", command=self.update_method_view).pack(anchor="w")
        tk.Radiobutton(frame, text="Método de Dos Fases", variable=self.method, value="Two Phase", command=self.update_method_view).pack(anchor="w")

        tk.Button(frame, text="Continuar", command=self.create_widgets).pack(pady=10)

    def update_method_view(self):
        """Updates the view dynamically based on selected method"""
        self.create_widgets()

    def create_widgets(self):
        """Displays the input fields based on the method selected"""
        # Clear the previous frame
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create a new frame for input fields
        frame = tk.Frame(self.root)
        frame.pack(pady=10, padx=10)

        # Display the method switcher at the top
        tk.Label(frame, text="Cambiar método:").grid(row=0, column=0, columnspan=2)
        tk.Radiobutton(frame, text="Método Simplex", variable=self.method, value="Simplex", command=self.update_method_view).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(frame, text="Método Gran M", variable=self.method, value="Big M", command=self.update_method_view).grid(row=1, column=1, sticky="w")
        tk.Radiobutton(frame, text="Método de Dos Fases", variable=self.method, value="Two Phase", command=self.update_method_view).grid(row=1, column=2, sticky="w")

        # Inputs for number of variables, number of constraints, and objective function coefficients
        tk.Label(frame, text="Número de variables:").grid(row=2, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.entry_vars["n"]).grid(row=2, column=1)

        tk.Label(frame, text="Número de restricciones:").grid(row=3, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.entry_vars["m"]).grid(row=3, column=1)

        tk.Label(frame, text="Coeficientes de la función objetivo:").grid(row=4, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.entry_vars["c"]).grid(row=4, column=1)

        # Add method-specific fields
        method = self.method.get()

        if method == "Simplex":
            tk.Label(frame, text="Simplex: Configuración específica no requerida").grid(row=5, column=0, columnspan=2)
        elif method == "Big M":
            tk.Label(frame, text="Gran M: Configuración específica").grid(row=5, column=0, columnspan=2)
            # You can add specific fields here if needed for Big M
        elif method == "Two Phase":
            tk.Label(frame, text="Dos Fases: Configuración específica").grid(row=5, column=0, columnspan=2)
            # You can add specific fields here if needed for Two Phase

        # Button to dynamically generate fields for constraints
        tk.Button(frame, text="Generar campos de restricciones", command=self.crear_campos_restricciones).grid(row=6, columnspan=2, pady=10)

        # Text widget for displaying the solution
        self.text_widget = tk.Text(self.root, height=20, width=60)
        self.text_widget.pack(pady=10)

        # Button to solve using the selected method
        tk.Button(self.root, text="Resolver", command=self.resolver).pack(pady=10)

        # Create another frame for constraint fields
        self.constraints_frame = frame

    def crear_campos_restricciones(self):
        """Generates input fields for constraints dynamically"""
        # Clear previous constraint fields
        for widget in self.constraints_frame.winfo_children():
            widget.destroy()

        self.restricciones_entries.clear()

        try:

            m = int(self.entry_vars["m"].get())
            n = int(self.entry_vars["n"].get())

            #self.method_frame = self.show_method_selector()
            tk.Label(self.constraints_frame, text="Cambiar método:").grid(row=3, column=2, columnspan=2)
            tk.Radiobutton(self.constraints_frame, text="Método Simplex", variable=self.method, value="Simplex", command=self.update_method_view).grid(row=1, column=2, sticky="w")
            tk.Radiobutton(self.constraints_frame, text="Método Gran M", variable=self.method, value="Big M", command=self.update_method_view).grid(row=2, column=2, sticky="w")
            tk.Radiobutton(self.constraints_frame, text="Método de Dos Fases", variable=self.method, value="Two Phase", command=self.update_method_view).grid(row=3, column=2, sticky="w")
            
            for i in range(m):

                restriccion_var_A = tk.StringVar()
                restriccion_var_b = tk.StringVar()
                
                self.restricciones_entries.append({"A": restriccion_var_A, "b": restriccion_var_b})

                # Add labels and entry fields for each constraint inside the 'constraints_frame' using grid
                tk.Label(self.constraints_frame, text=f"Restricción {i+1} coeficientes:").grid(row=i * 2, column=0, sticky="e")
                tk.Entry(self.constraints_frame, textvariable=restriccion_var_A).grid(row=i * 2, column=1)

                tk.Label(self.constraints_frame, text=f"Restricción {i+1} lado derecho:").grid(row=i * 2 + 1, column=0, sticky="e")
                tk.Entry(self.constraints_frame, textvariable=restriccion_var_b).grid(row=i * 2 + 1, column=1)
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores válidos.")
            self.create_widgets()

    def resolver(self):
        """Solves the problem using the selected method"""
        # Clear the text widget before displaying new results
        self.text_widget.delete(1.0, tk.END)

        try:
            # Retrieve input data
            n = int(self.entry_vars["n"].get())  # Number of variables
            m = int(self.entry_vars["m"].get())  # Number of constraints
            c = list(map(float, self.entry_vars["c"].get().split()))  # Objective function coefficients
            
            # Check the length of c
            if len(c) != n:
                messagebox.showerror("Error", f"Se esperaban {n} coeficientes para la función objetivo.")
                return

            # Retrieve coefficients matrix A and right-hand side values b
            A = [list(map(float, entry["A"].get().split())) for entry in self.restricciones_entries]
            b = [float(entry["b"].get()) for entry in self.restricciones_entries]

            # Check lengths of A and b
            if len(A) != m or any(len(row) != n for row in A):
                messagebox.showerror("Error", f"Se esperaban {m} restricciones, cada una con {n} coeficientes.")
                return
            if len(b) != m:
                messagebox.showerror("Error", f"Se esperaban {m} valores en el lado derecho de las restricciones.")
                return

            # Determine which method to use
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
                solver = Simplex.TwoPhaseSolver(n, m, c, A, b)
                solver.solve_with_two_phase(self.text_widget)
            else:
                messagebox.showerror("Error", "Método no soportado.")
        except ValueError as ve:
            messagebox.showerror("Error", f"Por favor ingrese valores válidos: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error: {e}")


# Run the Tkinter App
if __name__ == "__main__":
    root = tk.Tk()
    app = SimplexApp(root)
    root.mainloop()
