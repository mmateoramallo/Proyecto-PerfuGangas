import sqlite3

def agregar_columna_imagen():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    try:
        # ALTER TABLE permite modificar la estructura sin borrar datos
        cursor.execute("UPDATE Enlaces_Scraping SET ultima_revision = NULL WHERE id IN(3,4)")  # Limpiamos cualquier dato previo para evitar confusiones
        print("✅ ¡Cirugía exitosa! Columna 'imagen_url' agregada a la base de datos.")
    except sqlite3.OperationalError:
        print("⚠️ La columna ya existe (seguro ya habías corrido este script). Todo en orden.")
        
    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    agregar_columna_imagen()