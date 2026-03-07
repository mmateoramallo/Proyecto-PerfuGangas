import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

# ==========================================
# 1. FUNCIÓN EXTRACTORA PARA JULERIAQUE
# ==========================================
def obtener_precio_juleriaque(page, url, presentacion):
    try:
        page.goto(url, timeout=30000) # Le damos hasta 30 segundos para cargar si la red está lenta
        page.wait_for_selector('div.ProductPrice_priceContainer__iNDqq', timeout=15000)
        
        if presentacion != "Única":
            try:
                page.wait_for_timeout(3000)
                boton_tamano = page.get_by_text(presentacion).locator("visible=true").first
                
                if boton_tamano.is_visible():
                    boton_tamano.scroll_into_view_if_needed()
                    boton_tamano.click(force=True)
                    page.wait_for_timeout(2000)
                else:
                    print(f"   [!] El botón para {presentacion} no está visible (¿Sin stock?).")
            except Exception as e:
                print(f"   [!] Error al intentar seleccionar el tamaño {presentacion}: {e}")

        html_completo = page.content()
        sopa = BeautifulSoup(html_completo, 'html.parser')
        elemento_precio = sopa.find('div', class_='ProductPrice_priceContainer__iNDqq')

        if elemento_precio:
            precio_normal = elemento_precio.find('p', attrs={'data-fs-price': 'true'})
            precio_descuento = elemento_precio.find('p', attrs={'data-fs-highlight-price': 'true'})
            
            texto_precio = None
            if precio_descuento:
                texto_precio = precio_descuento.text.strip()
            elif precio_normal:
                texto_precio = precio_normal.text.strip()
            
            if texto_precio:
                precio_limpio = texto_precio.replace('$', '').replace('.', '').strip()
                return float(precio_limpio)
                
    except Exception as e:
        print(f"   [!] Error al cargar {url}: {e}")
        
    return None

# ==========================================
# 2. EL MOTOR PRINCIPAL (Director de Orquesta)
# ==========================================
def ejecutar_scraper_masivo():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    
    cursor.execute('''
        SELECT Enlaces_Scraping.id, Enlaces_Scraping.url, Tiendas.nombre, Perfumes.nombre, Perfumes.presentacion
        FROM Enlaces_Scraping
        JOIN Tiendas ON Enlaces_Scraping.id_tienda = Tiendas.id
        JOIN Perfumes ON Enlaces_Scraping.id_perfume = Perfumes.id
    ''')
    lista_enlaces = cursor.fetchall()
    
    if not lista_enlaces:
        print("No hay enlaces configurados en la base de datos.")
        conexion.close()
        return

    total_perfumes = len(lista_enlaces)
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Iniciando extracción masiva de precios ({fecha_hoy})...")
    print(f"📊 Total a procesar: {total_perfumes} presentaciones.")
    print("-" * 40)
    
    with sync_playwright() as p:
        # Lo ponemos visible para que puedas monitorearlo al principio si quieres
        browser = p.chromium.launch(headless=False) 
        
        for index, fila in enumerate(lista_enlaces, start=1):
            id_enlace = fila[0]
            url = fila[1]
            nombre_tienda = fila[2]
            nombre_perfume = fila[3]
            presentacion = fila[4]
            
            print(f"\n🔍 [{index}/{total_perfumes}] Buscando: {nombre_perfume} ({presentacion}) en {nombre_tienda}")
            
            # Usamos un contexto nuevo por cada iteración (Incógnito)
            context = browser.new_context()
            page = context.new_page()
            
            precio_obtenido = None
            
            if nombre_tienda == "Juleriaque":
                precio_obtenido = obtener_precio_juleriaque(page, url, presentacion)
            
            if precio_obtenido:
                cursor.execute('''
                    INSERT INTO Historial_Precios (id_enlace, precio, fecha)
                    VALUES (?, ?, ?)
                ''', (id_enlace, precio_obtenido, fecha_hoy))
                
                conexion.commit()
                print(f"   ✅ ¡Guardado! Precio: ${precio_obtenido}")
            else:
                print("   ❌ No se pudo extraer el precio.")
                
            context.close() # Cerramos el contexto para liberar memoria RAM
            
            # EL FRENO DE MANO: Pausa aleatoria antes del siguiente perfume
            tiempo_espera = random.uniform(4.0, 8.0)
            print(f"   ⏳ Descansando {tiempo_espera:.2f} segundos...")
            time.sleep(tiempo_espera)
            
        browser.close()
        
    conexion.close()
    print("\n🏁 Proceso de scraping finalizado al 100%.")

if __name__ == "__main__":
    ejecutar_scraper_masivo()