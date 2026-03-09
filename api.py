from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI(title="API de PerfuGangas")

# ==========================================
# CONFIGURACIÓN CORS (Permite que el Frontend hable con la API)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se pone la URL de tu web, aquí permitimos todo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def obtener_conexion():
    conexion = sqlite3.connect('perfugangas.db', check_same_thread=False)
    conexion.row_factory = sqlite3.Row 
    return conexion

# ==========================================
# RUTAS DEL MESERO
# ==========================================

@app.get("/")
def ruta_raiz():
    return {"mensaje": "¡Bienvenido a la API de PerfuGangas!"}

# 1. RUTA DE BÚSQUEDA (El motor de la barra principal)
@app.get("/buscaaar")
def buscar_perfume(q: str = ""):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Usamos LIKE en SQL para buscar coincidencias parciales (ej: "bleu" encuentra "Bleu de Chanel")
    query = f"%{q}%"
    cursor.execute('''
        SELECT id, nombre, marca, presentacion, imagen_url 
        FROM Perfumes 
        WHERE (nombre LIKE ? OR marca LIKE ?) AND activo = 1
    ''', (query, query))
    
    resultados = cursor.fetchall()
    conexion.close()
    
    return [dict(fila) for fila in resultados]


# 1. RUTA DE BÚSQUEDA (El motor de la barra principal)
@app.get("/buscar")
def buscar_perfume(q: str = ""):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    query = f"%{q}%"
    
    # TRUCO MAESTRO: Una "Subconsulta" para buscar el último precio de cada perfume
    cursor.execute('''
        SELECT p.id, p.nombre, p.marca, p.presentacion, p.imagen_url,
               (SELECT precio FROM Historial_Precios h
                JOIN Enlaces_Scraping e ON h.id_enlace = e.id
                WHERE e.id_perfume = p.id
                ORDER BY fecha DESC LIMIT 1) as precio_actual
        FROM Perfumes p 
        WHERE (p.nombre LIKE ? OR p.marca LIKE ?) AND p.activo = 1
    ''', (query, query))
    
    resultados = cursor.fetchall()
    conexion.close()
    
    return [dict(fila) for fila in resultados]


# 2. RUTA DEL HISTORIAL (Para dibujar el gráfico comparativo)
@app.get("/historial/{perfume_id}")
def obtener_historial(perfume_id: int):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Traemos todos los registros sueltos
    cursor.execute('''
        SELECT Tiendas.nombre as tienda, Historial_Precios.precio, Historial_Precios.fecha
        FROM Perfumes
        JOIN Enlaces_Scraping ON Perfumes.id = Enlaces_Scraping.id_perfume
        JOIN Tiendas ON Enlaces_Scraping.id_tienda = Tiendas.id
        JOIN Historial_Precios ON Enlaces_Scraping.id = Historial_Precios.id_enlace
        WHERE Perfumes.id = ?
        ORDER BY Historial_Precios.fecha ASC
    ''', (perfume_id,))
    
    resultados = cursor.fetchall()
    conexion.close()
    
    # ==========================================
    # MAGIA DE AGRUPACIÓN (Pivot)
    # ==========================================
    datos_agrupados = {}
    
    for fila in resultados:
        fecha = fila['fecha']
        tienda = fila['tienda']
        precio = fila['precio']
        
        # Si es el primer precio que vemos en esta fecha, creamos la cajita
        if fecha not in datos_agrupados:
            datos_agrupados[fecha] = {'fecha': fecha}
            
        # Agregamos el precio con una etiqueta especial (Ej: "precio_Juleriaque" o "precio_Fiorani")
        datos_agrupados[fecha][f"precio_{tienda}"] = precio

    # Convertimos nuestro diccionario agrupado en una lista final ordenada
    lista_final = sorted(datos_agrupados.values(), key=lambda x: x['fecha'])
    
    return lista_final