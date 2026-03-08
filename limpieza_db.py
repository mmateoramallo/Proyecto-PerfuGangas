import sqlite3

def aplicar_soft_delete():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    # 1. Agregamos la columna 'activo'
    try:
        # DEFAULT 1 significa que todo perfume nuevo o existente se asume activo por defecto
        cursor.execute("ALTER TABLE Perfumes ADD COLUMN activo INTEGER DEFAULT 1;")
        print("✅ Columna 'activo' agregada a la base de datos.")
    except sqlite3.OperationalError:
        print("⚠️ La columna 'activo' ya existía. Todo en orden.")

    # 2. Desactivamos los "fantasmas" (los que no tienen URL de imagen)
    cursor.execute("UPDATE Perfumes SET activo = 0 WHERE imagen_url IS NULL OR imagen_url = '';")
    filas_afectadas = cursor.rowcount
    
    conexion.commit()
    conexion.close()
    
    print(f"🧹 Limpieza lista: Se ocultaron {filas_afectadas} perfumes antiguos/fantasmas.")

if __name__ == "__main__":
    aplicar_soft_delete()