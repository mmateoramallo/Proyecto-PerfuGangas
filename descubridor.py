import sqlite3
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

def guardar_descubrimiento(nombre_perfume, marca, presentacion, url_completa):
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    cursor.execute('SELECT id FROM Tiendas WHERE nombre="Juleriaque"')
    resultado_tienda = cursor.fetchone()
    if not resultado_tienda:
        return
    id_juleriaque = resultado_tienda[0]

    cursor.execute('SELECT id FROM Perfumes WHERE nombre=? AND marca=? AND presentacion=?', (nombre_perfume, marca, presentacion))
    resultado_perfume = cursor.fetchone()
    
    if resultado_perfume:
        id_perfume = resultado_perfume[0]
    else:
        cursor.execute('INSERT INTO Perfumes (nombre, marca, presentacion) VALUES (?, ?, ?)', (nombre_perfume, marca, presentacion))
        id_perfume = cursor.lastrowid
        print(f"   🆕 Nuevo registrado: {marca} - {nombre_perfume} ({presentacion})")

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
    
    print(f"🚀 Iniciando escaneo masivo (Modo Visible e Incógnito)...")
    
    with sync_playwright() as p:
        # ¡CLAVE 1! headless=False nos permite ver si hay bloqueos y engaña mejor al servidor
        browser = p.chromium.launch(headless=False)
        
        while True:
            url_pagina = f"{url_base}{pagina_actual}"
            print(f"\n--- Explorando Página {pagina_actual} ---")
            
            # ¡CLAVE 2! Creamos un contexto nuevo (como una pestaña de incógnito limpia) por cada página
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            exito_carga = False
            for intento in range(max_reintentos):
                try:
                    print(f"Navegando a: {url_pagina} (Intento {intento + 1}/{max_reintentos})")
                    page.goto(url_pagina, timeout=30000)
                    
                    page.wait_for_selector('article[data-testid="fs-product-card"]', timeout=15000)
                    exito_carga = True
                    break
                    
                except Exception as e:
                    print(f"[!] Error al cargar la página: {e}")
                    if intento < max_reintentos - 1:
                        espera_error = 20
                        print(f"Esperando {espera_error} segundos antes de reintentar...")
                        time.sleep(espera_error)
            
            if not exito_carga:
                print(f"No se pudieron cargar más productos en la página {pagina_actual}. Asumiendo fin del catálogo.")
                context.close()
                break
            
            page.mouse.wheel(0, 4000)
            time.sleep(3) 
            
            html_completo = page.content()

            sopa = BeautifulSoup(html_completo, 'html.parser')
            tarjetas = sopa.find_all('article', attrs={'data-testid': 'fs-product-card'})
            
            if len(tarjetas) == 0:
                print("Página vacía detectada. Fin del escaneo.")
                context.close()
                break
                
            print(f"¡Se encontraron {len(tarjetas)} tarjetas en la página {pagina_actual}!")
            
            nuevos_enlaces_esta_pagina = 0
            for tarjeta in tarjetas:
                try:
                    marca = tarjeta.find('h3', attrs={'data-id': 'brand-name'}).text.strip()
                    nombre = tarjeta.find('h2', attrs={'data-id': 'product-name'}).text.strip()
                    
                    etiqueta_a = tarjeta.find('a', attrs={'data-fs-link': 'true'})
                    enlace_relativo = etiqueta_a['href']
                    url_completa = "https://www.juleriaque.com.ar" + enlace_relativo
                    
                    contenedor_variantes = tarjeta.find('div', attrs={'data-id': 'presentation-variants'})
                    presentaciones = []
                    
                    if contenedor_variantes:
                        variantes = contenedor_variantes.find_all('div', attrs={'data-fs-product-card-sku-variant': 'true'})
                        for v in variantes:
                            presentaciones.append(v.text.strip())
                    
                    if not presentaciones:
                        presentaciones.append("Única")
                        
                    for presentacion in presentaciones:
                        guardar_descubrimiento(nombre, marca, presentacion, url_completa)
                        nuevos_enlaces_esta_pagina += 1
                    
                except Exception as e:
                    pass
                    
            total_enlaces_procesados += nuevos_enlaces_esta_pagina
            print(f"Fin de la página {pagina_actual}. Se procesaron {nuevos_enlaces_esta_pagina} tamaños.")
            
            # Cerramos el "incógnito" para borrar cookies y no ser rastreados
            context.close()
            
            tiempo_espera = random.uniform(5.0, 10.0)
            print(f"Descansando {tiempo_espera:.2f} segundos para no saturar al servidor...")
            time.sleep(tiempo_espera)
            
            pagina_actual += 1

        browser.close()

    print("=" * 40)
    print(f"🏁 ESCANEO MASIVO FINALIZADO.")
    print(f"Se procesaron un total de {total_enlaces_procesados} perfumes/tamaños en todas las páginas exploradas.")

if __name__ == "__main__":
    url_hombres_masivo = "https://www.juleriaque.com.ar/fragancias?category-1=fragancias&category-2=premium&category-2=low-cost&category-3=masculinas&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Ccategory-3%2Cfuzzy%2Coperator&sort=score_desc&page="
    
    escanear_catalogo_completo(url_hombres_masivo)