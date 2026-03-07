import sqlite3

def configurar_base_datos():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tiendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Perfumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            marca TEXT,
            presentacion TEXT
        )
    ''')

    # CORRECCIÓN AQUÍ: Quitamos UNIQUE de url y agregamos UNIQUE(id_perfume, id_tienda)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Enlaces_Scraping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_perfume INTEGER,
            id_tienda INTEGER,
            url TEXT,
            FOREIGN KEY (id_perfume) REFERENCES Perfumes(id),
            FOREIGN KEY (id_tienda) REFERENCES Tiendas(id),
            UNIQUE(id_perfume, id_tienda)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Historial_Precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_enlace INTEGER,
            precio REAL,
            fecha TEXT,
            FOREIGN KEY (id_enlace) REFERENCES Enlaces_Scraping(id)
        )
    ''')

    # Datos iniciales
    cursor.execute('INSERT OR IGNORE INTO Tiendas (nombre) VALUES (?)', ("Juleriaque",))
    cursor.execute('SELECT id FROM Tiendas WHERE nombre="Juleriaque"')
    id_juleriaque = cursor.fetchone()[0]

    cursor.execute('INSERT INTO Perfumes (nombre, marca, presentacion) VALUES (?, ?, ?)', ("Spicebomb Dark Leather", "Viktor & Rolf", "Única"))
    id_spicebomb = cursor.lastrowid 

    cursor.execute('INSERT INTO Perfumes (nombre, marca, presentacion) VALUES (?, ?, ?)', ("Solo Loewe Cedro EDT", "Loewe", "Única"))
    id_loewe = cursor.lastrowid 

    cursor.execute('INSERT OR IGNORE INTO Enlaces_Scraping (id_perfume, id_tienda, url) VALUES (?, ?, ?)', (id_spicebomb, id_juleriaque, "https://www.juleriaque.com.ar/spicebomb-dark-leather-901952-15544/p"))
    cursor.execute('INSERT OR IGNORE INTO Enlaces_Scraping (id_perfume, id_tienda, url) VALUES (?, ?, ?)', (id_loewe, id_juleriaque, "https://www.juleriaque.com.ar/solo-loewe-cedro-edt-20594-572/p"))

    conexion.commit()
    print("✅ ¡Base de datos estructurada e inicializada con éxito (Bug de URL única corregido)!")
    conexion.close()

if __name__ == "__main__":
    configurar_base_datos()