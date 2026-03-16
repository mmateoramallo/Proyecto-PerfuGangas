import sqlite3
import time
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ==========================================
# 1. FUNCIÓN LIMPIADORA DE PRECIOS
# ==========================================
def limpiar_precio(texto_precio):
    if not texto_precio:
        return None
    numeros = re.findall(r'\d+', texto_precio)
    if numeros:
        return int("".join(numeros))
    return None

# ==========================================
# 2. LOS "MINIONS" EXTRACTORES
# ==========================================

# --- EL MINION DE JULERIAQUE ---
def obtener_precio_juleriaque(page, url, presentacion):
    try:
        # 1. wait_until="domcontentloaded" ignora la carga del video de YouTube
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        
        # Esperamos a que el contenedor del precio exista
        page.wait_for_selector('[data-fs-price-container="true"], [data-fs-price="true"]', timeout=15000)
        
        if presentacion != "Única":
            try:
                page.wait_for_timeout(2000)
                # 2. Apuntamos directamente al texto de la presentación (el span)
                boton_tamano = page.get_by_text(presentacion, exact=True).first
                
                if boton_tamano.is_visible():
                    boton_tamano.scroll_into_view_if_needed()
                    # 3. Forzamos el clic para atravesar pop-ups
                    boton_tamano.click(force=True)
                    
                    # Damos 2.5 segundos para que la página procese el clic y cambie el precio en el HTML
                    page.wait_for_timeout(2500)
            except Exception:
                pass

        html_completo = page.content()
        sopa = BeautifulSoup(html_completo, 'html.parser')
        
        precio_tag = sopa.find(attrs={'data-fs-highlight-price': 'true'}) or \
                     sopa.find(attrs={'data-id': 'spot-price'}) or \
                     sopa.find(attrs={'data-fs-price': 'true'})
        
        if precio_tag:
            precio_limpio = limpiar_precio(precio_tag.text)
            return precio_limpio, "OK"
            
        return None, "AGOTADO"
    except Exception as e:
        return None, "ERROR"

# --- EL MINION DE FIORANI ---
def obtener_precio_fiorani(page, url):
    try:
        page.goto(url, timeout=30000)
        selector_precio = '[class*="sellingPriceValue"]'
        selector_agotado = 'button:has-text("No disponible"), button:has-text("Avisarme"), div:has-text("Sin stock")'
        
        elemento = page.wait_for_selector(f"{selector_precio}, {selector_agotado}", timeout=15000)
        texto_elemento = elemento.inner_text().upper()
        
        if "NO DISPONIBLE" in texto_elemento or "AVISARME" in texto_elemento or "SIN STOCK" in texto_elemento:
            return None, "AGOTADO"
        
        texto_precio = page.locator(selector_precio).first.inner_text()
        return limpiar_precio(texto_precio), "OK"
        
    except Exception as e:
        return None, "ERROR"

# --- EL MINION DE PARFUMERIE (NUEVO) ---
def obtener_precio_parfumerie(page, url):
    try:
        page.goto(url, timeout=30000)
        
        # Parfumerie usa Magento 2. Buscamos el precio final o etiquetas de "Agotado"
        selector_precio = 'span[data-price-type="finalPrice"] > span.price, .price-final_price .price'
        selector_agotado = 'div.stock.unavailable, span:has-text("Agotado"), span:has-text("Sin stock")'
        
        elemento = page.wait_for_selector(f"{selector_precio}, {selector_agotado}", timeout=15000)
        texto_elemento = elemento.inner_text().upper()
        
        # Comprobamos si el texto atrapado indica falta de stock
        if "AGOTADO" in texto_elemento or "SIN STOCK" in texto_elemento or "UNAVAILABLE" in texto_elemento:
            return None, "AGOTADO"
        
        # Si no está agotado, extraemos el precio
        texto_precio = page.locator(selector_precio).first.inner_text()
        return limpiar_precio(texto_precio), "OK"
        
    except Exception as e:
        return None, "ERROR"


# ==========================================
# 3. EL CEREBRO PRINCIPAL (Enrutador + Logs)
# ==========================================
def ejecutar_scraper():
    conexion = sqlite3.connect('perfugangas.db')
    cursor = conexion.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    cursor.execute('''
            SELECT e.id, e.url, e.id_tienda, p.nombre, p.presentacion, e.ultima_revision
            FROM Enlaces_Scraping e
            JOIN Perfumes p ON e.id_perfume = p.id
            WHERE p.activo = 1
        ''')
    enlaces = cursor.fetchall()
    
    # Filtramos los que ya revisamos HOY
    enlaces_pendientes = [enlace for enlace in enlaces if enlace[5] != fecha_hoy]

    print(f"🚀 Iniciando extracción: {len(enlaces_pendientes)} enlaces pendientes hoy...")

    with open("errores_scraper.txt", "a", encoding="utf-8") as archivo_errores, sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 

        for index, (id_enlace, url, id_tienda, nombre, presentacion, ultima_revision) in enumerate(enlaces_pendientes, start=1):
            
            # Identificamos el nombre de la tienda
            if id_tienda == 1:
                nombre_tienda = "Juleriaque"
            elif id_tienda == 2:
                nombre_tienda = "Fiorani"
            elif id_tienda == 3:
                nombre_tienda = "Parfumerie"
            else:
                nombre_tienda = "Desconocida"

            print(f"\n🔍 [{index}/{len(enlaces_pendientes)}] Escaneando en {nombre_tienda}: [{nombre} - {presentacion}]...")
            
            context = browser.new_context()
            page = context.new_page()
            
            precio = None
            estado = "ERROR"
            
            # Enrutador
            if id_tienda == 1:
                precio, estado = obtener_precio_juleriaque(page, url, presentacion)
            elif id_tienda == 2:
                precio, estado = obtener_precio_fiorani(page, url)
            elif id_tienda == 3:
                precio, estado = obtener_precio_parfumerie(page, url)

            # Lógica de guardado
            if estado == "OK" and precio:
                cursor.execute('INSERT INTO Historial_Precios (id_enlace, precio, fecha) VALUES (?, ?, ?)',
                               (id_enlace, precio, fecha_hoy))
                print(f"  ✅ Precio guardado: ${precio:,}")
            elif estado == "AGOTADO":
                print("  ⚠️ Producto sin stock. Saltando...")
            elif estado == "ERROR":
                print(f"  [!] Error de extracción (Timeout). Guardado en errores_scraper.txt")
                archivo_errores.write(f"[{fecha_hoy}] ERROR en {nombre_tienda} | {nombre} ({presentacion}) | URL: {url}\n")

            cursor.execute('UPDATE Enlaces_Scraping SET ultima_revision = ? WHERE id = ?', (fecha_hoy, id_enlace))
            conexion.commit()

            context.close()
            tiempo_espera = random.uniform(2.0, 5.0)
            print(f"  ⏳ Descansando {tiempo_espera:.2f} seg...")
            time.sleep(tiempo_espera)

        browser.close()

    conexion.close()
    print("="*40)
    print("🏁 Extracción Multi-Tienda Finalizada.")

if __name__ == "__main__":
    ejecutar_scraper()