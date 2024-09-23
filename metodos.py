# Método Simplex y funciones auxiliares
def obtener_datos():
    print("Método Simplex - Programación Lineal (Maximización en Forma Estándar)")
    
    # Número de variables
    n = int(input("Ingrese el número de variables: "))
    
    # Número de restricciones (igualdades)
    m = int(input("Ingrese el número de restricciones: "))
    
    # Coeficientes de la función objetivo
    print("Ingrese los coeficientes de la función objetivo (ej. si es 3x1 + 2x2, ingrese: 3 2):")
    c = list(map(float, input().split()))
    
    # Coeficientes de las restricciones (igualdades)
    A = []
    b = []
    for i in range(m):
        print(f"Ingrese los coeficientes de la restricción {i+1} (ej. si es 2x1 + 3x2 = 5, ingrese: 2 3):")
        A.append(list(map(float, input().split())))
        b_val = float(input(f"Ingrese el lado derecho de la restricción {i+1} (ej. si es = 5, ingrese: 5): "))
        b.append(b_val)
    
    return n, m, c, A, b

def imprimir_tabla(tabla):
    print("Tabla Simplex:")
    for fila in tabla:
        print("\t".join(map("{:.2f}".format, fila)))
    print()

def pivot(tabla, row, col):
    pivot_element = tabla[row][col]
    tabla[row] = [x / pivot_element for x in tabla[row]]
    
    for i in range(len(tabla)):
        if i != row:
            ratio = tabla[i][col]
            tabla[i] = [tabla[i][j] - ratio * tabla[row][j] for j in range(len(tabla[i]))]

def simplex(n, m, c, A, b):
    tabla = [[0] * (n + m + 1) for _ in range(m + 1)]
    
    for i in range(m):
        tabla[i][:n] = A[i]        
        tabla[i][n + i] = 1        
        tabla[i][-1] = b[i]        

    tabla[-1][:n] = [-ci for ci in c]
    
    imprimir_tabla(tabla)
    
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
            raise Exception("Problema no acotado, no hay solución óptima.")
        
        print(f"Pivote en fila {row+1}, columna {col+1}")
        pivot(tabla, row, col)
        imprimir_tabla(tabla)
    
    solucion = [0] * n
    for i in range(n):
        columna = [tabla[j][i] for j in range(m)]
        if columna.count(1) == 1 and columna.count(0) == m - 1:
            fila = columna.index(1)
            solucion[i] = tabla[fila][-1]
    
    valor_optimo = tabla[-1][-1]
    
    return solucion, valor_optimo

def resolver_simplex():
    n, m, c, A, b = obtener_datos()
    
    try:
        solucion, valor_optimo = simplex(n, m, c, A, b)
        print("Solución óptima:")
        for i in range(n):
            print(f"x{i+1} = {solucion[i]:.4f}")
        print(f"Valor óptimo de la función objetivo: {valor_optimo:.4f}")
    except Exception as e:
        print(e)

# Menú
def mostrar_menu():
    print("Menú de opciones:")
    print("1. Metodo Simplex")
    print("2. Metodo de las 2 fases ")
    print("3. Metodo M grande")
    print("4. Salir")

def ejecutar_opcion(opcion):
    if opcion == "1":
        print("Has elegido el metodo Simplex.")
        resolver_simplex()  # Ejecuta el método Simplex cuando elige la opción 1
    elif opcion == "2":
        print("Has elegido el metodo de las 2 fases.")
    elif opcion == "3":
        print("Has elegido el metodo M grande.")
    elif opcion == "4":
        print("Saliendo del programa...")
    else:
        print("Opción no válida, por favor elige de nuevo.")

def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ")
        if opcion == "4":
            ejecutar_opcion(opcion)
            break
        ejecutar_opcion(opcion)

if __name__ == "__main__":
    main()
