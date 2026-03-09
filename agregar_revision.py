import sqlite3

def agregar_columna_revision():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    try:
        cursor.execute("ALTER TABLE Enlaces_Scraping ADD COLUMN ultima_revision TEXT;")
        print("✅ Columna 'ultima_revision' agregada perfectamente.")
    except sqlite3.OperationalError:
        print("⚠️ La columna ya existía.")
    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    agregar_columna_revision()