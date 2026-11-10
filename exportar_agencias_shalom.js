/*
 * Exporta las agencias que muestra https://shalom.com.pe/agencias (pestaña "Agencias").
 *
 * Cómo usarlo:
 *   1. Abre https://shalom.com.pe/agencias en Chrome o Edge y espera a que cargue la lista.
 *   2. Presiona F12 y entra a la pestaña "Console".
 *   3. Pega todo este código y presiona Enter.
 *      (La primera vez Chrome puede pedir que escribas "allow pasting" o "permitir pegar".)
 *   4. Se descargará el archivo agencias_web_shalom.json. Muévelo a la carpeta del proyecto
 *      y ejecuta:  python actualizar_agencias.py agencias_web_shalom.json
 *
 * Solo lee lo que la página ya cargó en tu navegador. No cambia nada en la web de Shalom.
 */
(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const CATEGORIA = /^(grande\s*\/\s*co|mediana|peque[ñn]a|micro|mini-micro|agente|punto pro|solo env[ií]os)$/i;

  function descargar(contenido) {
    const blob = new Blob([JSON.stringify(contenido, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'agencias_web_shalom.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  // 1) Datos completos que la página ya tiene en memoria (incluye coordenadas y el campo "web")
  function desdeLaApp() {
    const host = [...document.querySelectorAll('*')].find((e) => e.__vue_app__);
    if (!host) return null;
    // En producción Vue no guarda la instancia raíz en la app, pero sí el nodo raíz en el contenedor
    const raiz = host.__vue_app__._instance || (host._vnode && host._vnode.component);
    if (!raiz) return null;
    const esAgencia = (o) => o && typeof o === 'object' && !Array.isArray(o) && 'ter_id' in o && 'web' in o;
    const valor = (v) => (v && typeof v === 'object' && '__v_isRef' in v ? v.value : v);
    let mejorLista = null;
    const sueltas = new Map();
    const revisar = (v) => {
      v = valor(v);
      if (Array.isArray(v) && v.length && esAgencia(v[0])) {
        if (!mejorLista || v.length > mejorLista.length) mejorLista = v;
      } else if (esAgencia(v)) {
        sueltas.set(v.ter_id, v);
      }
    };
    const vistos = new Set();
    const pila = [raiz];
    while (pila.length) {
      const inst = pila.pop();
      if (!inst || vistos.has(inst)) continue;
      vistos.add(inst);
      for (const fuente of [inst.setupState, inst.props, inst.data, inst.exposed]) {
        if (!fuente) continue;
        for (const k of Object.keys(fuente)) {
          try { revisar(fuente[k]); } catch { /* propiedad no legible */ }
        }
      }
      const recorrer = (vn) => {
        if (!vn || typeof vn !== 'object') return;
        if (vn.props) Object.values(vn.props).forEach((v) => { try { revisar(v); } catch { /* sin acceso */ } });
        if (vn.component) pila.push(vn.component);
        if (vn.suspense && vn.suspense.activeBranch) recorrer(vn.suspense.activeBranch);
        if (Array.isArray(vn.children)) vn.children.forEach(recorrer);
        if (Array.isArray(vn.dynamicChildren)) vn.dynamicChildren.forEach(recorrer);
      };
      recorrer(inst.subTree);
    }
    const lista = mejorLista && mejorLista.length >= sueltas.size ? mejorLista : [...sueltas.values()];
    return lista.length ? JSON.parse(JSON.stringify(lista)) : null;
  }

  // 2) Respaldo: leer la lista visible en pantalla (nombre, dirección y categoría)
  async function desdeLaLista() {
    const hoja = [...document.querySelectorAll('body *')].find((el) => !el.children.length && CATEGORIA.test(el.textContent.trim()));
    if (!hoja) return null;
    let item = hoja;
    while (item.parentElement && [...item.parentElement.querySelectorAll('*')].filter((e) => !e.children.length && CATEGORIA.test(e.textContent.trim())).length <= 1) {
      item = item.parentElement;
    }
    const lista = item.parentElement;
    let scroller = lista;
    while (scroller && !(scroller.scrollHeight > scroller.clientHeight + 5 && /(auto|scroll)/.test(getComputedStyle(scroller).overflowY))) scroller = scroller.parentElement;
    const encontrados = new Map();
    const leer = () => {
      for (const el of lista.children) {
        const lineas = el.innerText.split('\n').map((t) => t.trim()).filter(Boolean);
        if (!lineas.length) continue;
        const categoria = lineas.find((t) => CATEGORIA.test(t)) || '';
        const textos = lineas.filter((t) => t !== categoria);
        const clave = textos.join(' | ');
        if (!encontrados.has(clave)) encontrados.set(clave, { nombre: textos[0] || '', direccion: textos.slice(1).join(' '), categoria });
      }
    };
    leer();
    if (scroller) {
      scroller.scrollTop = 0;
      await sleep(400);
      let quietos = 0;
      while (quietos < 4) {
        const antes = encontrados.size;
        scroller.scrollTop += Math.max(200, scroller.clientHeight * 0.8);
        await sleep(350);
        leer();
        const alFinal = scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 5;
        quietos = encontrados.size === antes && alFinal ? quietos + 1 : 0;
      }
    }
    return [...encontrados.values()];
  }

  console.log('Leyendo agencias de shalom.com.pe ...');
  const completas = desdeLaApp();
  if (completas) {
    const visibles = completas.filter((a) => a.web === 1 && a.agente === 0 && a.puntospro === 0);
    descargar({ fuente: 'app', pagina: location.href, fecha: new Date().toISOString(), total_catalogo: completas.length, total_visibles: visibles.length, agencias: completas });
    console.log(`Listo: ${visibles.length} agencias visibles en la pestaña "Agencias" (de ${completas.length} en el catálogo). Se descargó agencias_web_shalom.json`);
    return;
  }
  const lista = await desdeLaLista();
  if (lista && lista.length) {
    descargar({ fuente: 'lista', pagina: location.href, fecha: new Date().toISOString(), total_visibles: lista.length, agencias: lista });
    console.log(`Listo: ${lista.length} agencias leídas de la lista. Se descargó agencias_web_shalom.json`);
    return;
  }
  console.error('No se encontró la lista de agencias. Espera a que cargue la página, deja seleccionada la pestaña "Agencias" sin texto en el buscador y vuelve a intentarlo.');
})();
