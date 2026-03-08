import sqlite3
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

# Modificamos la función para que ahora reciba la imagen_url
def guardar_descubrimiento(nombre_perfume, marca, presentacion, url_completa, imagen_url):
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    cursor.execute('SELECT id FROM Tiendas WHERE nombre="Juleriaque"')
    resultado_tienda = cursor.fetchone()
    if not resultado_tienda:
        return
    id_juleriaque = resultado_tienda[0]

    # Preguntamos si el perfume ya existe y si tiene imagen
    cursor.execute('SELECT id, imagen_url FROM Perfumes WHERE nombre=? AND marca=? AND presentacion=?', (nombre_perfume, marca, presentacion))
    resultado_perfume = cursor.fetchone()
    
    if resultado_perfume:
        id_perfume = resultado_perfume[0]
        imagen_actual = resultado_perfume[1]
        
        # EL TRUCO: Si ya existe pero no tiene foto, se la actualizamos (UPDATE)
        if not imagen_actual:
            cursor.execute('UPDATE Perfumes SET imagen_url=? WHERE id=?', (imagen_url, id_perfume))
            print(f"   📸 Foto agregada a: {nombre_perfume} ({presentacion})")
    else:
        # Si es un perfume 100% nuevo, lo insertamos con foto y todo
        cursor.execute('INSERT INTO Perfumes (nombre, marca, presentacion, imagen_url) VALUES (?, ?, ?, ?)', (nombre_perfume, marca, presentacion, imagen_url))
        id_perfume = cursor.lastrowid
        print(f"   🆕 Nuevo registrado con foto: {marca} - {nombre_perfume} ({presentacion})")

    cursor.execute('''
        INSERT OR IGNORE INTO Enlaces_Scraping (id_perfume, id_tienda, url) 
        VALUES (?, ?, ?)
    ''', (id_perfume, id_juleriaque, url_completa))
    
    conexion.commit()
    conexion.close()

def escanear_catalogo_completo(url_base):
    pagina_actual = 0
    total_enlaces_procesados = 0
    max_reintentos = 3
    
    print(f"🚀 Iniciando escaneo masivo de Fotos (Modo Visible e Incógnito)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        while True:
            url_pagina = f"{url_base}{pagina_actual}"
            print(f"\n--- Explorando Página {pagina_actual} ---")
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            exito_carga = False
            for intento in range(max_reintentos):
                try:
                    page.goto(url_pagina, timeout=30000)
                    page.wait_for_selector('article[data-testid="fs-product-card"]', timeout=15000)
                    exito_carga = True
                    break
                except Exception as e:
                    if intento < max_reintentos - 1:
                        time.sleep(20)
            
            if not exito_carga:
                print(f"Fin del catálogo detectado en la página {pagina_actual}.")
                context.close()
                break
            
            page.mouse.wheel(0, 4000)
            time.sleep(3) 
            
            html_completo = page.content()
            sopa = BeautifulSoup(html_completo, 'html.parser')
            tarjetas = sopa.find_all('article', attrs={'data-testid': 'fs-product-card'})
            
            if len(tarjetas) == 0:
                context.close()
                break
                
            nuevos_enlaces_esta_pagina = 0
            for tarjeta in tarjetas:
                try:
                    marca = tarjeta.find('h3', attrs={'data-id': 'brand-name'}).text.strip()
                    nombre = tarjeta.find('h2', attrs={'data-id': 'product-name'}).text.strip()
                    
                    etiqueta_a = tarjeta.find('a', attrs={'data-fs-link': 'true'})
                    enlace_relativo = etiqueta_a['href']
                    url_completa = "https://www.juleriaque.com.ar" + enlace_relativo
                    
                    # === TU DESCUBRIMIENTO: EXTRAER LA FOTO ===
                    etiqueta_img = tarjeta.find('img', attrs={'data-fs-image': 'true'})
                    # Si encuentra la imagen saca el 'src', sino le pone un texto vacío
                    imagen_url = etiqueta_img['src'] if etiqueta_img else ""
                    # ==========================================
                    
                    contenedor_variantes = tarjeta.find('div', attrs={'data-id': 'presentation-variants'})
                    presentaciones = []
                    
                    if contenedor_variantes:
                        variantes = contenedor_variantes.find_all('div', attrs={'data-fs-product-card-sku-variant': 'true'})
                        for v in variantes:
                            presentaciones.append(v.text.strip())
                    
                    if not presentaciones:
                        presentaciones.append("Única")
                        
                    for presentacion in presentaciones:
                        # Le pasamos la imagen_url a nuestra función de base de datos
                        guardar_descubrimiento(nombre, marca, presentacion, url_completa, imagen_url)
                        nuevos_enlaces_esta_pagina += 1
                    
                except Exception as e:
                    pass
                    
            total_enlaces_procesados += nuevos_enlaces_esta_pagina
            
            context.close()
            time.sleep(random.uniform(5.0, 10.0))
            pagina_actual += 1

        browser.close()

    print("=" * 40)
    print(f"🏁 ESCANEO DE FOTOS FINALIZADO.")

if __name__ == "__main__":
    url_hombres_masivo = "https://www.juleriaque.com.ar/fragancias?category-1=fragancias&category-2=premium&category-2=low-cost&category-3=masculinas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Ccategory-3%2Cfuzzy%2Coperator&sort=score_desc&page="
    escanear_catalogo_completo(url_hombres_masivo)