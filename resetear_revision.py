import sqlite3

def resetear_errores():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()

    consultas = ['%invictus-parfum%', '%invictus-edt%', '%phantom-intense%']
    filas_afectadas = 0
    
    for consulta in consultas:
        # Agregamos "AND id_tienda = 1" para asegurar que solo modifique a Juleriaque
        cursor.execute('''
            UPDATE Enlaces_Scraping
            SET ultima_revision = ''
            WHERE url LIKE ? AND id_tienda = 1
        ''', (consulta,))
        filas_afectadas += cursor.rowcount

    conexion.commit()
    conexion.close()

    print(f"✅ Operación SQL exitosa. Se borró la fecha en {filas_afectadas} enlaces de Juleriaque.")

if __name__ == "__main__":
    resetear_errores()