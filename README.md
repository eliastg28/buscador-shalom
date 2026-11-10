# Buscador de Agencias Shalom

Aplicación 100 % frontend que lee un Excel o CSV de clientes de todo el Perú y sugiere la agencia Shalom más cercana a cada uno.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La aplicación completa (HTML, CSS y JavaScript). |
| `agencias_shalom.json` | Base de 494 agencias Shalom vigentes de los 25 departamentos, con dirección, referencia y coordenadas. |
| `exportar_agencias_shalom.js` | Script para la consola del navegador que exporta las agencias visibles en shalom.com.pe/agencias. |
| `actualizar_agencias.py` | Regenera `agencias_shalom.json` con esas agencias. |
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

La app debe usar **solo las agencias que muestra https://shalom.com.pe/agencias** (pestaña "Agencias"). Esa página cifra sus datos y no permite descargarlos automáticamente, así que la lista se exporta desde tu propio navegador:

1. Abre https://shalom.com.pe/agencias en Chrome o Edge y espera a que cargue la lista, sin escribir nada en el buscador.
2. Presiona **F12**, entra a **Console**, pega el contenido de `exportar_agencias_shalom.js` y presiona Enter. La primera vez Chrome puede pedir que escribas `allow pasting`.
3. Se descarga `agencias_web_shalom.json`. Muévelo a la carpeta del proyecto y ejecuta:

```bash
python actualizar_agencias.py agencias_web_shalom.json
git add agencias_shalom.json
git commit -m "Actualiza agencias Shalom"
git push
```

El script aplica el mismo filtro que la página oficial: publicadas en la web, sin agentes ni Puntos PRO. Las coordenadas se toman de la propia página y, si faltan, del catálogo de [shalom-api.lat](https://shalom-api.lat/docs/agencias). Al final lista las agencias que no se pudieron usar y el motivo.

Sin el archivo exportado, `python actualizar_agencias.py` arma una aproximación con las marcas internas del catálogo de shalom-api.lat.

Cada agencia tiene esta forma:

```json
{
  "id": "SH-258",
  "nombre": "Av Pachacutec",
  "departamento": "Cusco",
  "provincia": "Cusco",
  "distrito": "Wanchaq",
  "direccion": "Av. Pachacutec 429 - Wanchaq",
  "referencia": "A 100 Mtrs. de la Piscina Wanchaq",
  "latitud": -13.524396,
  "longitud": -71.970137,
  "categoria": "Micro",
  "horario": "Lunes a Viernes - 8:00 AM a 8:00 PM",
  "telefono": "(01) 500 7878",
  "ubigeo": 80108
}
```

Solo `nombre`, `latitud` y `longitud` son obligatorios. Para probar otra base sin publicarla, usa el botón **Cargar otro JSON de agencias**.

Herramienta independiente, sin afiliación con Shalom Empresarial S.A.C.
