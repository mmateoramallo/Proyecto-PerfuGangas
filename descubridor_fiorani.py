import sqlite3
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

# ==========================================
# 1. EL NORMALIZADOR (Filtro anti-duplicados)
# ==========================================
def normalizar_texto(texto):
    if not texto:
        return "Única"
    
    # Pasamos a mayúsculas y quitamos espacios en los extremos
    texto_limpio = texto.upper().strip()
    
    # Transformamos cosas como "100ml" o "100 ml" al formato estándar "100 ML"
    texto_limpio = re.sub(r'(\d+)\s*ML', r'\1 ML', texto_limpio)
    
    # Quitamos dobles espacios accidentales
    texto_limpio = " ".join(texto_limpio.split())
    
    return texto_limpio

# ==========================================
# 2. GUARDAR EN BASE DE DATOS
# ==========================================
def guardar_descubrimiento_fiorani(nombre_perfume, marca, presentacion, url_completa, imagen_url):
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    # 1. Asegurarnos de que la tienda exista
    cursor.execute('INSERT OR IGNORE INTO Tiendas (nombre) VALUES ("Fiorani")')
    cursor.execute('SELECT id FROM Tiendas WHERE nombre="Fiorani"')
    id_fiorani = cursor.fetchone()[0]

    # 2. Normalizamos los textos antes de buscar/guardar
    nombre_norm = normalizar_texto(nombre_perfume)
    marca_norm = normalizar_texto(marca)
    present_norm = normalizar_texto(presentacion)

    # 3. Buscamos si el perfume ya existe (creado por Juleriaque antes)
    cursor.execute('SELECT id, imagen_url FROM Perfumes WHERE nombre=? AND marca=? AND presentacion=?', 
                   (nombre_norm, marca_norm, present_norm))
    resultado_perfume = cursor.fetchone()
    
    if resultado_perfume:
        id_perfume = resultado_perfume[0]
        imagen_actual = resultado_perfume[1]
        
        # Si ya existe pero no tiene foto de Juleriaque, le ponemos la de Fiorani
        if not imagen_actual and imagen_url:
            cursor.execute('UPDATE Perfumes SET imagen_url=?, activo=1 WHERE id=?', (imagen_url, id_perfume))
        else:
            cursor.execute('UPDATE Perfumes SET activo=1 WHERE id=?', (id_perfume,))
    else:
        # Si es un perfume 100% nuevo que solo tiene Fiorani, lo creamos
        cursor.execute('INSERT INTO Perfumes (nombre, marca, presentacion, imagen_url, activo) VALUES (?, ?, ?, ?, 1)', 
                       (nombre_norm, marca_norm, present_norm, imagen_url))
        id_perfume = cursor.lastrowid
        print(f"   🆕 Nuevo perfume encontrado en Fiorani: {marca_norm} - {nombre_norm} ({present_norm})")

    # 4. Guardamos el enlace específico de Fiorani
    cursor.execute('''
        INSERT OR IGNORE INTO Enlaces_Scraping (id_perfume, id_tienda, url) 
        VALUES (?, ?, ?)
    ''', (id_perfume, id_fiorani, url_completa))
    
    conexion.commit()
    conexion.close()

# ==========================================
# 3. EL NAVEGADOR (Crawler)
# ==========================================
def escanear_fiorani(url_base):
    pagina_actual = 1 # A diferencia de Juleriaque, Fiorani suele paginar desde el 1
    total_enlaces = 0
    max_reintentos = 3
    
    print("🚀 Iniciando escaneo en FIORANI (Modo Visible)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        while True:
            # Le inyectamos el &page= al final de la URL compleja de Fiorani
            url_pagina = f"{url_base}&page={pagina_actual}"
            print(f"\n--- Explorando Fiorani Página {pagina_actual} ---")
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            exito = False
            for intento in range(max_reintentos):
                try:
                    page.goto(url_pagina, timeout=30000)
                    # Esperamos que aparezca al menos una tarjeta (usamos una parte de la clase)
                    page.wait_for_selector('.vtex-product-summary-2-x-element', timeout=15000)
                    exito = True
                    break
                except Exception as e:
                    if intento < max_reintentos - 1:
                        time.sleep(10)
            
            if not exito:
                print(f"Fin del catálogo detectado en la página {pagina_actual}.")
                context.close()
                break
            
            # Scroll para cargar las imágenes perezosas
            page.mouse.wheel(0, 4000)
            time.sleep(3)
            
            sopa = BeautifulSoup(page.content(), 'html.parser')
            # Usamos Regex (re.compile) para buscar cualquier clase que contenga este texto
            tarjetas = sopa.find_all('section', class_=re.compile(r'vtex-product-summary-2-x-container'))
            
            if not tarjetas:
                context.close()
                break
                
            nuevos_esta_pagina = 0
            for tarjeta in tarjetas:
                try:
                    marca_tag = tarjeta.find('span', class_=re.compile(r'vtex-store-components-3-x-productBrandName'))
                    nombre_tag = tarjeta.find('span', class_=re.compile(r'vtex-product-summary-2-x-brandName'))
                    link_tag = tarjeta.find('a', class_=re.compile(r'vtex-product-summary-2-x-clearLink'))
                    img_tag = tarjeta.find('img', class_=re.compile(r'vtex-product-summary-2-x-imageNormal'))
                    
                    if not nombre_tag or not link_tag:
                        continue
                        
                    marca_cruda = marca_tag.text.strip() if marca_tag else "DESCONOCIDA"
                    nombre_crudo = nombre_tag.text.strip()
                    url_completa = "https://www.fiorani.com" + link_tag['href']
                    imagen_url = img_tag['src'] if img_tag else ""
                    
                    variantes = tarjeta.find_all('div', class_=re.compile(r'vtex-product-summary-2-x-skuSelectorItemTextValue'))
                    presentaciones_crudas = [v.text.strip() for v in variantes]
                    
                    if not presentaciones_crudas:
                        presentaciones_crudas.append("Única")
                        
                    for pres in presentaciones_crudas:
                        guardar_descubrimiento_fiorani(nombre_crudo, marca_cruda, pres, url_completa, imagen_url)
                        nuevos_esta_pagina += 1
                        
                except Exception as e:
                    print(f"Error procesando una tarjeta en Fiorani: {e}")
                    
            total_enlaces += nuevos_esta_pagina
            print(f"Fin página {pagina_actual}. Procesados {nuevos_esta_pagina} tamaños.")
            
            context.close()
            time.sleep(random.uniform(5.0, 8.0))
            pagina_actual += 1
            
        browser.close()
        
    print("="*40)
    print(f"🏁 ESCANEO DE FIORANI FINALIZADO. Total procesado: {total_enlaces}")

if __name__ == "__main__":
    url_fiorani = "https://www.fiorani.com/fragancias?initialMap=c&initialQuery=fragancias&map=category-1,category-2&query=/fragancias/fragancias-masculinas"
    escanear_fiorani(url_fiorani)