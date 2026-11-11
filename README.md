# Buscador de Agencias Shalom

Aplicación 100 % frontend que lee los pedidos desde Google Sheets (en tiempo real) o desde un Excel o CSV y sugiere la agencia Shalom más cercana a cada cliente.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La aplicación completa (HTML, CSS y JavaScript). |
| `google_sheets_apps_script.gs` | Código para pegar en Apps Script de tu Google Sheets: conecta la hoja de pedidos con la app. |
| `agencias_shalom.json` | Las 496 agencias que muestra shalom.com.pe/agencias, con dirección, referencia, categoría y coordenadas. |
| `exportar_agencias_shalom.js` | Script para la consola del navegador que exporta las agencias visibles en shalom.com.pe/agencias. |
| `actualizar_agencias.py` | Regenera `agencias_shalom.json` a partir del HTML guardado de shalom.com.pe/agencias. |
| `generar_excel_prueba.py` | Genera `clientes_prueba_peru.xlsx` con 13 clientes de prueba (formato antiguo). |
| `clientes_prueba_peru.xlsx` | Excel de prueba ya generado. |

## Google Sheets

La app puede leer los pedidos directamente de tu Google Sheets. Los pedidos nuevos aparecen solos (la hoja se revisa cada 30 segundos) y se procesan automáticamente, empezando por los más recientes. Cada pedido tiene un **Estado** (*Pendiente*, *En atención* o *Atendido*): lo cambias en la app y se guarda en la columna ESTADO de tu hoja. Los pedidos *Atendido* no se vuelven a procesar.

Instalación, una sola vez:

1. Abre tu Google Sheets de pedidos. Los títulos deben estar en la primera fila y los pedidos en la primera pestaña. Si están en otra pestaña, escribe su nombre en `HOJA_PEDIDOS` al inicio del código.
2. Ve a **Extensiones → Apps Script**. Borra lo que haya, pega todo el contenido de `google_sheets_apps_script.gs` y guarda (Ctrl+S). Basta con tener acceso de **editor** a la hoja.
   - Si tienes varias cuentas de Google abiertas, Apps Script puede mostrar "Sorry, unable to open the file at this time". Haz la instalación en una ventana de incógnito, entrando solo con la cuenta que tiene acceso a la hoja.
   - Otra opción, sin agregar nada al archivo: entra a [script.google.com](https://script.google.com), crea un **Nuevo proyecto**, pega el código y escribe en `ID_HOJA` el ID de la hoja (la parte de su enlace entre `/d/` y `/edit`).
3. En la barra de arriba elige la función **crearClave** y presiona **Ejecutar**. Google pedirá permisos: elige tu cuenta, luego **Configuración avanzada → Ir a (proyecto)** y **Permitir**. En el **Registro de ejecución** aparece tu clave: cópiala.
4. Presiona **Implementar → Nueva implementación**. En el engranaje elige **Aplicación web**. Configura **Ejecutar como: Yo** y **Quién tiene acceso: Cualquier usuario**. Presiona **Implementar** y copia la **URL de la aplicación web** (termina en `/exec`).
5. En la app, paso 2, elige **Google Sheets**, pega la URL y la clave y presiona **Conectar**. Con "Recordar" marcado, la app se conecta sola cada vez que la abras en ese navegador.

La primera vez que la app lee la hoja, crea la columna **ESTADO** al final con una lista desplegable. Cada pedido nuevo que llega sin estado queda como *Pendiente* en la hoja la próxima vez que la app la revisa (cada 30 segundos mientras está abierta). También puedes cambiar el estado directamente en la hoja: la app lo verá en la siguiente revisión.

Sobre la seguridad: la página de GitHub es pública, pero no guarda ningún pedido. Solo quien tenga la URL **y** la clave puede leer la hoja o cambiar estados. No compartas la clave; si se filtra, ejecuta otra vez `crearClave` y usa la nueva. Si cambias el código de Apps Script, publícalo otra vez en **Implementar → Gestionar implementaciones → Editar → Versión: Nueva versión**. Así la URL no cambia.

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

`NÚMERO DE TELÉFONO · NOMBRE Y APELLIDOS · DEPARTAMENTO · PROVINCIA · DISTRITO · DIRECCIÓN · REFERENCIA · PRODUCTO · PRECIO`

Las demás columnas se conservan en el Excel descargado. También se acepta el formato antiguo con una sola columna "Ciudad y/o Distrito".

## Lima y Callao

Los clientes de la provincia de Lima y de la provincia del Callao se entregan por motorizado. En los resultados puedes filtrar **Todos**, **Lima y Callao** o **Provincias**. El botón **Copiar mensaje** de un cliente de Lima o Callao arma el mensaje de motorizado con su dirección y el precio de la columna PRECIO. Los demás clientes reciben el mensaje con la agencia Shalom más cercana. Los dos mensajes se pueden editar en "Mensajes para WhatsApp". El Excel descargado incluye la columna "Tipo de Envío".

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

La app usa **solo las agencias que muestra https://shalom.com.pe/agencias** (pestaña "Agencias"). Esa página cifra sus datos y no permite descargarlos automáticamente, así que se guarda su HTML desde el navegador:

1. Abre https://shalom.com.pe/agencias en Chrome o Edge, deja la pestaña "Agencias" sin texto en el buscador y haz scroll en la lista hasta el final.
2. Presiona **F12**. En la pestaña **Elements**, haz clic derecho sobre la primera línea `<html>` y elige **Copy > Copy outerHTML**.
3. En VS Code crea el archivo `shalom_agencias.html` en la carpeta del proyecto, pega y guarda.
4. Ejecuta:

```bash
python actualizar_agencias.py shalom_agencias.html
git add agencias_shalom.json
git commit -m "Actualiza agencias Shalom"
git push
```

El script lee del HTML el nombre, la dirección, la referencia y la categoría de cada agencia. Las coordenadas las toma del catálogo de [shalom-api.lat](https://shalom-api.lat/docs/agencias), buscando cada agencia por nombre y dirección. Al final indica cuántas agencias usó y cuáles no pudo usar. El HTML no se sube a GitHub.

Alternativa: pegar `exportar_agencias_shalom.js` en la consola de esa página genera `agencias_web_shalom.json`, que se usa igual: `python actualizar_agencias.py agencias_web_shalom.json`.

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
