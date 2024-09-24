import tkinter as tk
from tkinter import messagebox
import Simplex

class SimplexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Método Simplex - Programación Lineal")
        self.frame = ""

        self.entry_vars = {
            "n": tk.StringVar(),
            "m": tk.StringVar(),
            "c": tk.StringVar()
        }
        self.restricciones_entries = []

        self.create_widgets()

    def create_widgets(self):
        # Create a frame to use grid manager inside it
        frame = tk.Frame(self.root)
        frame.pack(pady=10, padx=10)

        # Inputs for number of variables, number of constraints, and objective function coefficients
        tk.Label(frame, text="Número de variables:").grid(row=0, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.entry_vars["n"]).grid(row=0, column=1)

        tk.Label(frame, text="Número de restricciones:").grid(row=1, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.entry_vars["m"]).grid(row=1, column=1)

        tk.Label(frame, text="Coeficientes de la función objetivo:").grid(row=2, column=0, sticky="e")
        tk.Entry(frame, textvariable=self.entry_vars["c"]).grid(row=2, column=1)

        # Button to dynamically generate fields for constraints
        tk.Button(frame, text="Generar campos de restricciones", command=self.crear_campos_restricciones).grid(row=3, columnspan=2, pady=10)

        # Text widget for displaying the solution
        self.text_widget = tk.Text(self.root, height=20, width=60)
        self.text_widget.pack(pady=10)

        # Button to solve the simplex method
        tk.Button(self.root, text="Resolver Simplex", command=self.resolver_simplex).pack(pady=10)

        # Create another frame for constraint fields
        self.constraints_frame = frame
        
    def crear_campos_restricciones(self):
        # Clear previous constraint fields
        for widget in self.constraints_frame.winfo_children():
            widget.destroy()

        self.restricciones_entries.clear()

        try:
            m = int(self.entry_vars["m"].get())
            n = int(self.entry_vars["n"].get())

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

    def resolver_simplex(self):
        self.text_widget.delete(1.0, tk.END)  
        try:
            n = int(self.entry_vars["n"].get())
            m = int(self.entry_vars["m"].get())
            c = list(map(float, self.entry_vars["c"].get().split()))
            A = [list(map(float, entry["A"].get().split())) for entry in self.restricciones_entries]
            b = [float(entry["b"].get()) for entry in self.restricciones_entries]

            solver = Simplex.SimplexSolver(n, m, c, A, b)
            solver.simplex(self.text_widget)
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error: {e}")

# Run the Tkinter App
if __name__ == "__main__":
    root = tk.Tk()
    app = SimplexApp(root)
    root.mainloop()