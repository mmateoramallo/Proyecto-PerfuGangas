import sqlite3
import time
import re
import unicodedata
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ID_TIENDA = 3 # ID correspondiente a Parfumerie

def normalizar_texto(texto):
    """Normaliza el texto para evitar duplicados en la base de datos por tildes o mayúsculas."""
    if not texto:
        return ""
    texto = str(texto).upper().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto

def extraer_volumen(texto_nombre, sopa_elemento):
    """Intenta extraer el tamaño (ej. 100 ML) del botón seleccionado o del nombre."""
    boton_swatch = sopa_elemento.find('div', class_='swatch-option text selected')
    if boton_swatch and boton_swatch.text:
        volumen = boton_swatch.text.strip().upper()
        volumen = re.sub(r'(\d+)\s*ML', r'\1 ML', volumen)
        return volumen

    match = re.search(r'(\d+)\s*ML', texto_nombre, re.IGNORECASE)
    if match:
        return f"{match.group(1)} ML"
        
    return "Única"

def escanear_parfumerie():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    urls_procesadas = set() 
    nuevos_enlaces = 0
    pagina = 1
    
    print("🚀 Iniciando Descubridor en Parfumerie...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()

        while True:
            url_catalogo = f"https://www.parfumerie.com.ar/catalog/category/view/s/masculinas/id/977/?p={pagina}"
            print(f"\n📄 Escaneando Página {pagina}: {url_catalogo}")
            
            try:
                page.goto(url_catalogo, timeout=40000)
                page.wait_for_load_state('networkidle', timeout=20000)
            except Exception as e:
                print(f"  [!] Error o fin de paginación en la página {pagina}: {e}")
                break 

            html = page.content()
            sopa = BeautifulSoup(html, 'html.parser')
            
            tarjetas = sopa.find_all('li', class_='product-item')
            
            if not tarjetas:
                print("  [!] No se encontraron más productos. Fin del catálogo.")
                break

            productos_en_pagina = 0

            for tarjeta in tarjetas:
                try:
                    # 1. Extracción de URL
                    enlace_tag = tarjeta.find('a', class_='product-item-photo')
                    if not enlace_tag or not enlace_tag.has_attr('href'):
                        continue
                    url_producto = enlace_tag['href']
                    
                    if url_producto in urls_procesadas:
                        continue
                    urls_procesadas.add(url_producto)
                    productos_en_pagina += 1

                    # 2. Extracción de Imagen
                    img_tag = tarjeta.find('img', class_='product-image-photo')
                    imagen_url = img_tag['src'] if img_tag else ""

                    # 3. Extracción de Marca
                    marca_tag = tarjeta.find('strong', class_='product-item-brand')
                    marca_bruta = marca_tag.text.strip() if marca_tag else "DESCONOCIDA"
                    marca_norm = normalizar_texto(marca_bruta)

                    # 4. Extracción de Nombre y Limpieza
                    nombre_tag = tarjeta.find('strong', class_='product-item-name')
                    nombre_bruto = nombre_tag.text.strip() if nombre_tag else "SIN NOMBRE"
                    
                    presentacion = extraer_volumen(nombre_bruto, tarjeta)
                    
                    nombre_limpio = re.sub(r'\b\d+\s*ML\b', '', nombre_bruto, flags=re.IGNORECASE)
                    nombre_limpio = nombre_limpio.replace("+ POUCH DE REGALO", "").replace("+ REGALO A ELECCIÓN", "")
                    nombre_norm = normalizar_texto(nombre_limpio)

                    print(f"  🔍 Detectado: {marca_norm} | {nombre_norm} ({presentacion})")

                    # ==========================================
                    # GUARDADO EN BASE DE DATOS CORREGIDO
                    # ==========================================
                    
                    # Buscamos por el nombre normalizado que guardaremos en la columna 'nombre'
                    cursor.execute('''SELECT id FROM Perfumes 
                                      WHERE nombre = ? AND presentacion = ?''', 
                                   (nombre_norm, presentacion))
                    resultado = cursor.fetchone()

                    if resultado:
                        id_perfume = resultado[0]
                        cursor.execute('SELECT imagen_url FROM Perfumes WHERE id = ?', (id_perfume,))
                        img_actual = cursor.fetchone()[0]
                        if not img_actual and imagen_url:
                            cursor.execute('UPDATE Perfumes SET imagen_url = ? WHERE id = ?', (imagen_url, id_perfume))
                    else:
                        cursor.execute('''INSERT INTO Perfumes (nombre, marca, presentacion, imagen_url, activo)
                                          VALUES (?, ?, ?, ?, 1)''',
                                       (nombre_norm, marca_norm, presentacion, imagen_url))
                        id_perfume = cursor.lastrowid

                    cursor.execute('SELECT id FROM Enlaces_Scraping WHERE url = ? AND id_tienda = ?', (url_producto, ID_TIENDA))
                    if not cursor.fetchone():
                        cursor.execute('''INSERT INTO Enlaces_Scraping (id_perfume, id_tienda, url, ultima_revision) 
                                          VALUES (?, ?, ?, '')''', (id_perfume, ID_TIENDA, url_producto))
                        nuevos_enlaces += 1
                        
                    conexion.commit()

                except Exception as e:
                    print(f"  [!] Error al procesar una tarjeta: {e}")

            if productos_en_pagina == 0:
                print("  [!] Fin del contenido único. Terminando paginación.")
                break
                
            pagina += 1
            time.sleep(3) 

        browser.close()
    
    conexion.close()
    print("="*40)
    print(f"🏁 Descubrimiento finalizado. Total enlaces de Parfumerie añadidos: {nuevos_enlaces}")

if __name__ == "__main__":
    escanear_parfumerie()