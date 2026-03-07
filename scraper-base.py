from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url_descuento = "https://www.juleriaque.com.ar/spicebomb-dark-leather-901952-15544/p"
url_normal = "https://www.juleriaque.com.ar/solo-loewe-cedro-edt-20594-572/p"

# Elige cuál URL probar aquí:
url_a_probar = url_normal 

with sync_playwright() as p:
    # 1. Abrimos un navegador Chromium. 
    # Si pones headless=False, ¡verás cómo se abre la ventana del navegador sola!
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print(f"Navegando a: {url_a_probar} ...")
    page.goto(url_a_probar)
    
    # 2. LA MAGIA: Le decimos que espere hasta que el contenedor del precio aparezca en pantalla.
    # Así le damos tiempo al JavaScript de hacer su trabajo.
    print("Esperando a que JavaScript cargue los datos...")
    page.wait_for_selector('div.ProductPrice_priceContainer__iNDqq', timeout=10000)
    
    # 3. Una vez que cargó, extraemos todo el HTML ya procesado.
    html_completo = page.content()
    
    # Cerramos el navegador para no consumir memoria
    browser.close()

# 4. Ahora volvemos a tu terreno seguro: BeautifulSoup
sopa = BeautifulSoup(html_completo, 'html.parser')
elemento_precio = sopa.find('div', class_='ProductPrice_priceContainer__iNDqq')

if elemento_precio:
    # 5. Adaptamos TU lógica para los dos casos
    precio_normal = elemento_precio.find('p', attrs={'data-fs-price': 'true'})
    precio_descuento = elemento_precio.find('p', attrs={'data-fs-highlight-price': 'true'})
    
    if precio_descuento:
         print(f"¡OFERTA ENCONTRADA! El precio final es: {precio_descuento.text.strip()}")
    elif precio_normal:
         print(f"¡Éxito! Precio regular encontrado: {precio_normal.text.strip()}")
    else:
         print("Encontré la caja, pero no los precios adentro.")
else:
    print("Uy, no pude encontrar la etiqueta del precio en el HTML.")