import sqlite3

def reparar_base_datos():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()

    try:
        # 1. Obligamos a Parfumerie a tener el ID 3
        cursor.execute("UPDATE Tiendas SET id = 3 WHERE nombre = 'Parfumerie'")
        
        # 2. Nos aseguramos de que todos los enlaces de Parfumerie apunten al ID 3
        # (Por si acaso el descubridor también guardó el 919)
        cursor.execute("UPDATE Enlaces_Scraping SET id_tienda = 3 WHERE url LIKE '%parfumerie.com.ar%'")
        
        conexion.commit()
        print("✅ ¡Reparación exitosa! Parfumerie ahora tiene el ID 3 y los enlaces están alineados.")
    except Exception as e:
        print(f"⚠️ Hubo un error: {e}")
    finally:
        conexion.close()

if __name__ == "__main__":
    reparar_base_datos()