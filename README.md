# Buscador de Agencias Shalom

Aplicación 100 % frontend que lee un Excel o CSV de clientes de todo el Perú y sugiere la agencia Shalom más cercana a cada uno.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La aplicación completa (HTML, CSS y JavaScript). |
| `agencias_shalom.json` | Base de 475 agencias Shalom de los 25 departamentos, con coordenadas. |
| `generar_excel_prueba.py` | Genera `clientes_prueba_peru.xlsx` con 13 clientes de prueba (formato antiguo). |
| `clientes_prueba_peru.xlsx` | Excel de prueba ya generado. |

## Publicar en GitHub Pages

1. Crea un repositorio y sube `index.html` y `agencias_shalom.json` a la raíz.
2. En el repositorio entra a **Settings → Pages**.
3. En **Source** elige **Deploy from a branch**, rama `main`, carpeta `/ (root)` y guarda.
4. En uno o dos minutos la app estará en `https://TU-USUARIO.github.io/NOMBRE-DEL-REPO/`.

## Probar en tu computadora

Si abres `index.html` con doble clic, el navegador no deja leer `agencias_shalom.json`; la app te pedirá cargarlo con un botón. Para evitarlo, levanta un servidor local en la carpeta:

```bash
python -m http.server 8000
```

Luego abre `http://localhost:8000`.

## Generar el Excel de prueba

```bash
pip install pandas openpyxl
python generar_excel_prueba.py
```

## Formato del archivo

La app detecta las columnas por su nombre. El formato recomendado es el de Pedidos Shopify:

`NÚMERO DE TELÉFONO · NOMBRE Y APELLIDOS · DEPARTAMENTO · PROVINCIA · DISTRITO · DIRECCIÓN · REFERENCIA`

Las demás columnas (producto, precio, etc.) se conservan en el Excel descargado. También se acepta el formato antiguo con una sola columna "Ciudad y/o Distrito".

## Cómo busca la ubicación de cada cliente

Departamento, provincia y distrito se consideran correctos (vienen de un combobox). La dirección puede tener errores de tipeo.

1. Ubica el distrito y busca la dirección **solo dentro de ese distrito**, para que un error de tipeo no lleve a otra ciudad.
2. Busca la dirección tal cual: `[Dirección], [Distrito], [Provincia], [Departamento], Perú`.
3. La normaliza (quita Mz/Lt/Int, expande "Av.", "Jr.", "Urb." y corrige errores comunes como "Avenidad", "Jiron", "Urbanisacion", "Av.Larco1045") y vuelve a buscar.
4. Si aún no hay número exacto, usa Photon, un buscador de OpenStreetMap que tolera errores de tipeo ("Ejersito" → Ejército, "Pisarro" → Pizarro).
5. Si la calle existe pero el número no, estima la ubicación por la numeración (≈100 números por cuadra) usando puntos de número conocido en la misma calle, incluidas las propias agencias Shalom.
6. Si no encuentra la calle, prueba con la urbanización o AA.HH. y con la referencia ("Mercado Modelo"). Referencias vagas como "frente al parque" se ignoran.
7. Como último recurso usa el centro del distrito y prioriza las agencias de ese distrito.

Todo resultado se compara con lo escrito por el cliente: si el nombre de la calle encontrada no se parece, se descarta. La columna **Precisión** indica cómo se ubicó cada cliente, y la **Observación** muestra la calle encontrada y si se corrigió un error de tipeo.

La distancia es en línea recta, calculada con la fórmula de Haversine.

## OpenStreetMap o Google Maps

- **OpenStreetMap (Nominatim)** es gratis. La app espera 1 segundo entre consultas, así que cada cliente toma de 1 a 5 segundos. Úsalo para decenas o pocos cientos de filas.
- **Google Maps** ubica mejor las direcciones con número. Necesitas una API Key con **Maps JavaScript API** y **Geocoding API** habilitadas y facturación activa. Restringe la clave por *HTTP referrer* a tu dominio `github.io`.

Las búsquedas se guardan en caché en el navegador durante 30 días, así que reprocesar un archivo es casi instantáneo.

## Actualizar la base de agencias

`agencias_shalom.json` tiene la forma:

```json
{
  "meta": { "fecha_extraccion": "2026-09-29" },
  "agencias": [
    {
      "id": "SH-001",
      "nombre": "Calle Liverpool",
      "departamento": "La Libertad",
      "provincia": "Trujillo",
      "distrito": "Trujillo",
      "direccion": "Calle liverpool n° 329 / urb. santa isabel - trujillo",
      "referencia": "A una cuadra antes de la iglesia de mansiche",
      "latitud": -8.103728,
      "longitud": -79.042822,
      "precision_coordenadas": "fuente",
      "horario_lv": "8:00 AM A 8:00 PM",
      "horario_dom": "8:00 AM A 5:00 PM",
      "telefono": "(01) 500 - 7878"
    }
  ]
}
```

Solo `nombre`, `latitud` y `longitud` son obligatorios. También se acepta una lista simple de agencias sin `meta`. Para probar otra base sin publicarla, usa el botón **Cargar otro JSON de agencias**.

Los datos se tomaron el 29/09/2026 de un listado público de agencias. 23 agencias no tenían coordenadas publicadas y se ubicaron de forma aproximada con OpenStreetMap; tienen `"precision_coordenadas": "aproximada"` y la app las marca en la tabla. Shalom abre y cierra agencias con frecuencia: confirma la agencia antes de enviar.

Herramienta independiente, sin afiliación con Shalom Empresarial S.A.C.
