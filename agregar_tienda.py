import sqlite3

def agregar_parfumerie():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    # Verificamos si ya existe para no duplicar
    cursor.execute("SELECT id FROM Tiendas WHERE nombre = 'Parfumerie'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO Tiendas (nombre) VALUES ('Parfumerie')")
        print("✅ Tienda 'Parfumerie' agregada a la base de datos con éxito.")
    else:
        print("⚠️ La tienda 'Parfumerie' ya existía en la base de datos.")
        
    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    agregar_parfumerie()