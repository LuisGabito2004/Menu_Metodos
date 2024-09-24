import tkinter as tk
from tkinter import messagebox

def obtener_datos(entry_vars, restricciones_entries):
    n = int(entry_vars["n"].get())
    m = int(entry_vars["m"].get())

    c = list(map(float, entry_vars["c"].get().split()))
    A = []
    b = []

    for i in range(m):
        A.append(list(map(float, restricciones_entries[i]["A"].get().split())))
        b.append(float(restricciones_entries[i]["b"].get()))

    return n, m, c, A, b

def imprimir_tabla(tabla, text_widget, iteracion):
    text_widget.insert(tk.END, f"Tabla Simplex - Iteración {iteracion}:\n")
    for fila in tabla:
        text_widget.insert(tk.END, "\t".join(map("{:.2f}".format, fila)) + "\n")
    text_widget.insert(tk.END, "\n")

def pivot(tabla, row, col):
    pivot_element = tabla[row][col]
    tabla[row] = [x / pivot_element for x in tabla[row]]

    for i in range(len(tabla)):
        if i != row:
            ratio = tabla[i][col]
            tabla[i] = [tabla[i][j] - ratio * tabla[row][j] for j in range(len(tabla[i]))]

def simplex(n, m, c, A, b, text_widget):
    iteracion = 1
    tabla = [[0] * (n + m + 1) for _ in range(m + 1)]

    for i in range(m):
        tabla[i][:n] = A[i]        
        tabla[i][n + i] = 1        
        tabla[i][-1] = b[i]        

    tabla[-1][:n] = [-ci for ci in c]

    imprimir_tabla(tabla, text_widget, iteracion)
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
            messagebox.showerror("Error", "Problema no acotado, no hay solución óptima.")
            return

        text_widget.insert(tk.END, f"Pivote en fila {row+1}, columna {col+1}\n")
        pivot(tabla, row, col)
        imprimir_tabla(tabla, text_widget, iteracion)
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

def resolver_simplex(entry_vars, restricciones_entries, text_widget):
    text_widget.delete(1.0, tk.END)  
    try:
        n, m, c, A, b = obtener_datos(entry_vars, restricciones_entries)
        simplex(n, m, c, A, b, text_widget)
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error: {e}")

def crear_interfaz():
    root = tk.Tk()
    root.title("Método Simplex - Programación Lineal")

    frame = tk.Frame(root)
    frame.pack(pady=10, padx=10)

    entry_vars = {
        "n": tk.StringVar(),
        "m": tk.StringVar(),
        "c": tk.StringVar()
    }

    tk.Label(frame, text="Número de variables:").grid(row=0, column=0, sticky="e")
    tk.Entry(frame, textvariable=entry_vars["n"]).grid(row=0, column=1)

    tk.Label(frame, text="Número de restricciones:").grid(row=1, column=0, sticky="e")
    tk.Entry(frame, textvariable=entry_vars["m"]).grid(row=1, column=1)

    tk.Label(frame, text="Coeficientes de la función objetivo:").grid(row=2, column=0, sticky="e")
    tk.Entry(frame, textvariable=entry_vars["c"]).grid(row=2, column=1)

    restricciones_entries = []

    def crear_campos_restricciones():
        for widget in frame.winfo_children():
            if str(widget).startswith(".!frame.!entry") and not widget in [entry_vars["n"], entry_vars["m"], entry_vars["c"]]:
                widget.grid_forget()
                
        restricciones_entries.clear()

        try:
            m = int(entry_vars["m"].get())
            n = int(entry_vars["n"].get())

            for i in range(m):
                restriccion_var_A = tk.StringVar()
                restriccion_var_b = tk.StringVar()

                restricciones_entries.append({"A": restriccion_var_A, "b": restriccion_var_b})

                tk.Label(frame, text=f"Restricción {i+1} coeficientes:").grid(row=3 + i * 2, column=0, sticky="e")
                tk.Entry(frame, textvariable=restriccion_var_A).grid(row=3 + i * 2, column=1)

                tk.Label(frame, text=f"Restricción {i+1} lado derecho:").grid(row=4 + i * 2, column=0, sticky="e")
                tk.Entry(frame, textvariable=restriccion_var_b).grid(row=4 + i * 2, column=1)
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores válidos para el número de variables y restricciones.")

    tk.Button(frame, text="Generar campos de restricciones", command=crear_campos_restricciones).grid(row=3, columnspan=2, pady=10)

    text_widget = tk.Text(root, height=20, width=60)
    text_widget.pack(pady=10)

    tk.Button(root, text="Resolver Simplex", command=lambda: resolver_simplex(entry_vars, restricciones_entries, text_widget)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz()
