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

# --- EL MINION DE JULERIAQUE (¡Tu código original restaurado!) ---
def obtener_precio_juleriaque(page, url, presentacion):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_selector('div.ProductPrice_priceContainer__iNDqq', timeout=15000)
        
        # Seleccionamos el tamaño haciendo clic en el botón
        if presentacion != "Única":
            try:
                page.wait_for_timeout(2000)
                boton_tamano = page.get_by_text(presentacion).locator("visible=true").first
                if boton_tamano.is_visible():
                    boton_tamano.scroll_into_view_if_needed()
                    boton_tamano.click(force=True)
                    page.wait_for_timeout(2000)
            except Exception as e:
                pass # Si no encuentra el botón, intentamos sacar el precio por defecto

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
                precio_limpio = limpiar_precio(texto_precio)
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
        # MODO VISIBLE ACTIVADO
        browser = p.chromium.launch(headless=False) 

        for index, (id_enlace, url, id_tienda, nombre, presentacion, ultima_revision) in enumerate(enlaces_pendientes, start=1):
            nombre_tienda = "Juleriaque" if id_tienda == 1 else "Fiorani"
            print(f"\n🔍 [{index}/{len(enlaces_pendientes)}] Escaneando en {nombre_tienda}: [{nombre} - {presentacion}]...")
            
            # INCÓGNITO: Abrimos y cerramos el contexto por cada perfume
            context = browser.new_context()
            page = context.new_page()
            
            precio = None
            estado = "ERROR"
            
            # Enrutador
            if id_tienda == 1:
                # Juleriaque SÍ necesita saber la presentación para hacer clic
                precio, estado = obtener_precio_juleriaque(page, url, presentacion)
            elif id_tienda == 2:
                # Fiorani usa el ?skuId en la URL, no necesita hacer clic
                precio, estado = obtener_precio_fiorani(page, url)

            # Lógica de guardado
            if estado == "OK" and precio:
                cursor.execute('INSERT INTO Historial_Precios (id_enlace, precio, fecha) VALUES (?, ?, ?)',
                               (id_enlace, precio, fecha_hoy))
                print(f"  ✅ Precio guardado: ${precio:,}")
            elif estado == "AGOTADO":
                print("  ⚠️ Producto sin stock. Saltando...")
            elif estado == "ERROR":
                print("  [!] Error de extracción (Timeout). Guardado en errores_scraper.txt")
                archivo_errores.write(f"[{fecha_hoy}] ERROR en {nombre_tienda} | {nombre} ({presentacion}) | URL: {url}\n")

            cursor.execute('UPDATE Enlaces_Scraping SET ultima_revision = ? WHERE id = ?', (fecha_hoy, id_enlace))
            conexion.commit()

            # Cerramos el incógnito y descansamos
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