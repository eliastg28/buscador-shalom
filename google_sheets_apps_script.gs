/**
 * Conecta tu Google Sheets de pedidos con el Buscador de Agencias Shalom.
 *
 * - La app lee los pedidos de la hoja (cada fila es un pedido).
 * - Cuando cambias el estado de un pedido en la app, se escribe en la columna ESTADO de la hoja.
 *   Si la columna no existe, se crea al final con una lista desplegable.
 * - Los pedidos nuevos que llegan sin estado quedan como "Pendiente" en la hoja.
 *
 * Instalación (una sola vez). Sirve con acceso de editor; no hace falta ser dueño de la hoja.
 *   1. Abre el editor de una de estas dos formas:
 *      a) Desde la hoja: Extensiones > Apps Script.
 *      b) Si (a) falla o no quieres agregar nada al archivo: entra a https://script.google.com,
 *         "Nuevo proyecto", y escribe abajo en ID_HOJA el ID de la hoja (la parte de su enlace
 *         entre /d/ y /edit).
 *      Borra lo que haya, pega todo este archivo y guarda (Ctrl+S).
 *   2. Arriba elige la función "crearClave" y presiona "Ejecutar". Autoriza con tu cuenta.
 *      En el "Registro de ejecución" aparece tu clave: cópiala.
 *   3. Implementar > Nueva implementación > tipo "Aplicación web".
 *      Ejecutar como: Yo. Quién tiene acceso: Cualquier usuario. Implementar.
 *      Copia la "URL de la aplicación web" (termina en /exec).
 *   4. En el buscador, paso 2 > Google Sheets, pega la URL y la clave y presiona Conectar.
 *
 * Sin la clave nadie puede leer ni cambiar tu hoja, aunque tenga la URL. No la compartas.
 * Si cambias este código, publica de nuevo: Implementar > Gestionar implementaciones > editar > Versión: nueva.
 */

// ID de la hoja de pedidos. Solo hace falta si el código NO se abrió desde Extensiones > Apps Script de la hoja.
// Ejemplo: en https://docs.google.com/spreadsheets/d/1AbC...xYz/edit el ID es 1AbC...xYz
const ID_HOJA = '';
// Nombre de la pestaña con los pedidos. Vacío = la primera pestaña del archivo.
const HOJA_PEDIDOS = '';
// Título de la columna de estado (se crea si no existe)
const TITULO_ESTADO = 'ESTADO';
// Estados por defecto. La app envía su propia lista, así que si cambias los estados en la app no hace
// falta tocar este código: la lista desplegable de la hoja se actualiza sola.
const ESTADOS = ['Pendiente', 'En atención', 'Sin respuesta', 'Seguimiento', 'Confirmado', 'Enviado', 'PAGADO'];

/** Ejecuta esta función una vez desde el editor para crear (o cambiar) la clave de acceso. */
function crearClave() {
  const clave = Utilities.getUuid().replace(/-/g, '').slice(0, 24);
  PropertiesService.getScriptProperties().setProperty('CLAVE', clave);
  console.log('Tu clave para el buscador es: ' + clave);
  return clave;
}

/** Ejecútala desde el editor para comprobar que el código llega a tu hoja de pedidos. */
function probarConexion() {
  const datos = leerPedidos();
  console.log('Conectado a "' + datos.libro + '", pestaña "' + datos.hoja + '": ' + datos.filas.length +
    ' pedidos. Columna de estado: ' + datos.encabezados[datos.columnaEstado] + '.');
}

function doGet(e) {
  return responder(function () {
    const p = (e && e.parameter) || {};
    verificarClave(p.clave);
    return leerPedidos(listaEstados(p.estados));
  });
}

function doPost(e) {
  return responder(function () {
    const datos = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    verificarClave(datos.clave);
    if (datos.accion === 'estado') return guardarEstado(datos);
    if (datos.accion === 'estados') return guardarEstados(datos);
    throw new Error('Acción no reconocida.');
  });
}

function responder(fn) {
  let salida;
  try {
    salida = Object.assign({ ok: true }, fn());
  } catch (err) {
    salida = { ok: false, error: String((err && err.message) || err) };
  }
  return ContentService.createTextOutput(JSON.stringify(salida)).setMimeType(ContentService.MimeType.JSON);
}

// Lista de estados enviada por la app (texto JSON o arreglo). Si no llega o no es válida, se usa ESTADOS.
function listaEstados(valor) {
  let lista = valor;
  try { if (typeof valor === 'string') lista = JSON.parse(valor); } catch (err) { lista = null; }
  if (!Array.isArray(lista)) return ESTADOS;
  lista = lista.map(function (x) { return String(x == null ? '' : x).trim(); })
    .filter(function (x) { return x && x.length <= 40; }).slice(0, 20);
  return lista.length ? lista : ESTADOS;
}

function verificarClave(clave) {
  const guardada = PropertiesService.getScriptProperties().getProperty('CLAVE');
  if (!guardada) throw new Error('Falta crear la clave: en Apps Script ejecuta la función crearClave.');
  if (!clave || String(clave) !== guardada) throw new Error('Clave incorrecta.');
}

function libroPedidos() {
  const libro = ID_HOJA ? SpreadsheetApp.openById(ID_HOJA) : SpreadsheetApp.getActiveSpreadsheet();
  if (!libro) throw new Error('El código no está dentro de la hoja: escribe su ID en ID_HOJA y vuelve a implementar.');
  return libro;
}

function hojaPedidos() {
  const libro = libroPedidos();
  const hoja = HOJA_PEDIDOS ? libro.getSheetByName(HOJA_PEDIDOS) : libro.getSheets()[0];
  if (!hoja) throw new Error('No existe la pestaña "' + HOJA_PEDIDOS + '".');
  return hoja;
}

function normalizar(texto) {
  return String(texto == null ? '' : texto)
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

// Fila de títulos: la primera (de las 10 primeras) con al menos 3 celdas escritas
function filaTitulos(valores) {
  for (let i = 0; i < Math.min(10, valores.length); i++) {
    if (valores[i].filter(function (c) { return String(c).trim() !== ''; }).length >= 3) return i;
  }
  return 0;
}

function columnaEstado(titulos) {
  return titulos.findIndex(function (t) {
    const n = normalizar(t);
    return n === 'estado' || n === 'estado de atencion' || n === 'estado del pedido' || n === 'estado pedido';
  });
}

// Crea la columna ESTADO al final, con lista desplegable
function crearColumnaEstado(hoja, filaTit, estados) {
  const col = hoja.getLastColumn() + 1;
  hoja.getRange(filaTit + 1, col).setValue(TITULO_ESTADO).setFontWeight('bold');
  aplicarListaEstados(hoja, filaTit, col - 1, estados);
  return col - 1;
}

function aplicarListaEstados(hoja, filaTit, colEstado, estados) {
  const filas = Math.max(hoja.getMaxRows() - filaTit - 1, 1);
  const regla = SpreadsheetApp.newDataValidation().requireValueInList(estados, true).setAllowInvalid(true).build();
  hoja.getRange(filaTit + 2, colEstado + 1, filas, 1).setDataValidation(regla);
}

// Si la lista desplegable de la hoja no tiene los estados actuales, se actualiza
function asegurarListaEstados(hoja, filaTit, colEstado, estados) {
  const regla = hoja.getRange(filaTit + 2, colEstado + 1).getDataValidation();
  const actual = regla ? regla.getCriteriaValues()[0] : null;
  if (Array.isArray(actual) && actual.join('|') === estados.join('|')) return;
  aplicarListaEstados(hoja, filaTit, colEstado, estados);
}

function leerPedidos(estados) {
  estados = estados || ESTADOS;
  const hoja = hojaPedidos();
  if (hoja.getLastRow() === 0) throw new Error('La hoja de pedidos está vacía.');
  let valores = hoja.getDataRange().getDisplayValues();
  const filaTit = filaTitulos(valores);
  let colEstado = columnaEstado(valores[filaTit]);
  if (colEstado < 0) {
    const lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try {
      valores = hoja.getDataRange().getDisplayValues();
      colEstado = columnaEstado(valores[filaTit]);
      if (colEstado < 0) {
        colEstado = crearColumnaEstado(hoja, filaTit, estados);
        SpreadsheetApp.flush();
        valores = hoja.getDataRange().getDisplayValues();
      }
    } finally {
      lock.releaseLock();
    }
  }
  asegurarListaEstados(hoja, filaTit, colEstado, estados);
  const titulos = valores[filaTit];
  const filas = [];
  const sinEstado = [];
  for (let i = filaTit + 1; i < valores.length; i++) {
    const fila = valores[i];
    const conDatos = fila.some(function (c, k) { return k !== colEstado && String(c).trim() !== ''; });
    if (!conDatos) continue;
    if (String(fila[colEstado]).trim() === '') {
      sinEstado.push(i + 1);
      fila[colEstado] = estados[0];
    }
    filas.push({ fila: i + 1, valores: fila });
  }
  if (sinEstado.length) marcarPendientes(hoja, sinEstado, colEstado, estados[0]);
  return {
    hoja: hoja.getName(),
    libro: libroPedidos().getName(),
    encabezados: titulos,
    columnaEstado: colEstado,
    estados: estados,
    filas: filas,
  };
}

// Los pedidos nuevos (estado vacío) quedan como "Pendiente" en la hoja
function marcarPendientes(hoja, filas, colEstado, pendiente) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    // Se vuelve a leer la columna por si alguien escribió un estado mientras tanto
    const actuales = hoja.getRange(1, colEstado + 1, hoja.getLastRow(), 1).getDisplayValues();
    const celdas = filas
      .filter(function (f) { return f <= actuales.length && String(actuales[f - 1][0]).trim() === ''; })
      .map(function (f) { return hoja.getRange(f, colEstado + 1).getA1Notation(); });
    if (celdas.length) hoja.getRangeList(celdas).setValue(pendiente);
  } finally {
    lock.releaseLock();
  }
}

function validarEstado(datos) {
  const estado = listaEstados(datos.estados).find(function (e) { return normalizar(e) === normalizar(datos.estado); });
  if (!estado) throw new Error('Estado no válido: ' + datos.estado);
  return estado;
}

// Lee la hoja una vez para ubicar uno o varios pedidos
function contextoHoja() {
  const hoja = hojaPedidos();
  const valores = hoja.getDataRange().getDisplayValues();
  const filaTit = filaTitulos(valores);
  const titulos = valores[filaTit];
  const colEstado = columnaEstado(titulos);
  if (colEstado < 0) throw new Error('No se encontró la columna ' + TITULO_ESTADO + '. Actualiza el buscador.');
  return { hoja: hoja, valores: valores, filaTit: filaTit, titulos: titulos, colEstado: colEstado };
}

// Devuelve el índice (desde 0) de la fila del pedido. La app envía la fila y algunos datos del pedido
// (teléfono, nombre) para comprobar que es el mismo; si la fila se movió (por ejemplo, se borró una
// fila de arriba), se busca el pedido por esos datos.
function ubicarPedido(ctx, fila, huellaDatos) {
  const huella = Object.keys(huellaDatos || {}).map(function (t) {
    return { col: ctx.titulos.findIndex(function (x) { return normalizar(x) === normalizar(t); }), valor: normalizar(huellaDatos[t]) };
  }).filter(function (h) { return h.col >= 0; });
  const coincide = function (f) {
    return huella.every(function (h) { return normalizar(f[h.col]) === h.valor; });
  };
  const indice = Number(fila) - 1;
  if (indice > ctx.filaTit && indice < ctx.valores.length && coincide(ctx.valores[indice])) return indice;
  const candidatos = [];
  if (huella.length) {
    for (let i = ctx.filaTit + 1; i < ctx.valores.length; i++) if (coincide(ctx.valores[i])) candidatos.push(i);
  }
  if (candidatos.length !== 1) throw new Error('El pedido cambió de lugar en la hoja. Presiona "Actualizar" y vuelve a intentarlo.');
  return candidatos[0];
}

function guardarEstado(datos) {
  const estado = validarEstado(datos);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ctx = contextoHoja();
    const indice = ubicarPedido(ctx, datos.fila, datos.huella);
    ctx.hoja.getRange(indice + 1, ctx.colEstado + 1).setValue(estado);
    return { fila: indice + 1, estado: estado };
  } finally {
    lock.releaseLock();
  }
}

// Varios pedidos al mismo estado, en una sola escritura. Devuelve el resultado de cada uno.
function guardarEstados(datos) {
  const estado = validarEstado(datos);
  const pedidos = Array.isArray(datos.pedidos) ? datos.pedidos.slice(0, 1000) : [];
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ctx = contextoHoja();
    const usadas = {};
    const resultados = pedidos.map(function (p) {
      try {
        const indice = ubicarPedido(ctx, p && p.fila, p && p.huella);
        if (usadas[indice]) throw new Error('Pedido repetido.');
        usadas[indice] = true;
        return { ok: true, fila: indice + 1 };
      } catch (err) {
        return { ok: false, error: String((err && err.message) || err) };
      }
    });
    const celdas = resultados.filter(function (r) { return r.ok; })
      .map(function (r) { return ctx.hoja.getRange(r.fila, ctx.colEstado + 1).getA1Notation(); });
    if (celdas.length) ctx.hoja.getRangeList(celdas).setValue(estado);
    return { estado: estado, resultados: resultados };
  } finally {
    lock.releaseLock();
  }
}
