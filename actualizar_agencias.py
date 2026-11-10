#!/usr/bin/env python3
"""
Actualiza agencias_shalom.json con el catálogo vigente de agencias Shalom.

Fuente: listado público de shalom-api.lat (https://shalom-api.lat/docs/agencias), que replica
el catálogo del sistema de Shalom (el mismo que muestra https://shalom.com.pe/agencias) y lo
refresca cada 3 horas. Es un endpoint de demostración sin API key: úsalo solo para actualizar
esta base de vez en cuando, no en cada visita a la app.

Uso (no requiere instalar nada):
    python actualizar_agencias.py shalom_agencias.html       # SOLO las agencias que muestra shalom.com.pe/agencias
    python actualizar_agencias.py agencias_web_shalom.json   # igual, con la exportación de exportar_agencias_shalom.js
    python actualizar_agencias.py                            # sin la página: aproxima con las marcas del catálogo

shalom_agencias.html es el HTML de https://shalom.com.pe/agencias copiado desde DevTools
(pestaña Elements, clic derecho en <html>, Copy > Copy outerHTML). Ver README.md.
"""
import json
import re
import sys
import unicodedata
import urllib.request
from difflib import SequenceMatcher
from html.parser import HTMLParser
from datetime import date
from pathlib import Path

URL = "https://api.shalom-api.lat/public/agencies"
SALIDA = Path(__file__).with_name("agencias_shalom.json")

DEPARTAMENTOS = {
    "AMAZONAS": "Amazonas", "ANCASH": "Áncash", "APURIMAC": "Apurímac", "AREQUIPA": "Arequipa",
    "AYACUCHO": "Ayacucho", "CAJAMARCA": "Cajamarca", "CALLAO": "Callao", "CUSCO": "Cusco",
    "HUANCAVELICA": "Huancavelica", "HUANUCO": "Huánuco", "ICA": "Ica", "JUNIN": "Junín",
    "LA LIBERTAD": "La Libertad", "LAMBAYEQUE": "Lambayeque", "LIMA": "Lima", "LORETO": "Loreto",
    "MADRE DE DIOS": "Madre de Dios", "MOQUEGUA": "Moquegua", "PASCO": "Pasco", "PIURA": "Piura",
    "PUNO": "Puno", "SAN MARTIN": "San Martín", "TACNA": "Tacna", "TUMBES": "Tumbes", "UCAYALI": "Ucayali",
}

# Registros internos que no son agencias de recojo para el cliente
EXCLUIR_NOMBRE = re.compile(
    r"aeropuerto|aperopuerto|^puerto\b|\bcaja\b|area shalom|prueba|cambio_de_nombre|por definir|"
    r"terminal de bus|almacenes|talleres",
    re.I,
)
EXCLUIR_CATEGORIA = {"PUNTO PRO", "SOLO ENVÍOS", "SOLO ENVIOS"}
# Categorías de la página oficial que no se sugieren al cliente: no son agencias de recojo
EXCLUIR_WEB = {"PUNTO PRO", "SOLO ENVIOS"}

MINUSCULAS = {"de", "del", "la", "las", "los", "el", "y", "e", "a", "al", "en", "con", "por"}
ROMANOS = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"}


def limpiar(texto):
    return re.sub(r"\s+", " ", str(texto or "").replace("\xa0", " ")).strip(" ,.-–")


def titulo(texto):
    """'AV. PACHACUTEC 429 - WANCHAQ' -> 'Av. Pachacutec 429 - Wanchaq'"""
    palabras = limpiar(texto).lower().split(" ")
    salida = []
    for i, p in enumerate(palabras):
        base = re.sub(r"[^a-záéíóúñü]", "", p)
        if base in ROMANOS and len(base) > 1:
            salida.append(p.upper())
        elif i > 0 and p in MINUSCULAS:
            salida.append(p)
        else:
            salida.append(re.sub(r"^([^a-záéíóúñü]*)([a-záéíóúñü])", lambda m: m.group(1) + m.group(2).upper(), p))
    return re.sub(r"\b(am|pm)\b", lambda m: m.group(1).upper(), " ".join(salida), flags=re.I)


def separar_referencia(direccion):
    """Shalom guarda la referencia dentro de la dirección: '..., REF. A 100 MTRS. DE LA PISCINA'."""
    texto = limpiar(direccion)
    m = re.search(r"[,\s]*\bREF(?:ERENCIA)?\b\s*[.:]*\s*", texto, re.I)
    if not m:
        return texto, ""
    return limpiar(texto[: m.start()]), limpiar(texto[m.end():])


def coordenada(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def sin_tildes(texto):
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()


def descargar_catalogo():
    print(f"Descargando {URL} ...")
    req = urllib.request.Request(URL, headers={"Accept": "application/json", "User-Agent": "buscador-agencias-shalom/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        datos = json.load(resp)
    crudas = datos.get("data") or []
    if not crudas:
        sys.exit("La respuesta no trae agencias; no se modificó agencias_shalom.json")
    return crudas


def armar(a):
    """Convierte un registro con los campos del sistema de Shalom al formato de la app."""
    lat, lng = coordenada(a.get("latitud")), coordenada(a.get("longitud"))
    direccion, referencia = separar_referencia(a.get("direccion"))
    dep = DEPARTAMENTOS.get(sin_tildes(limpiar(a.get("departamento")).upper()), titulo(a.get("departamento")))
    horario = limpiar(a.get("hora_atencion"))
    if limpiar(a.get("hora_domingo")):
        horario += f" | Domingo: {limpiar(a.get('hora_domingo'))}"
    return {
        "id": f"SH-{a.get('ter_id')}",
        "nombre": titulo(a.get("lugar_over") or a.get("nombre")),
        "departamento": dep,
        "provincia": titulo(a.get("provincia")),
        "distrito": titulo(a.get("zona")),
        "direccion": titulo(direccion),
        "referencia": titulo(referencia),
        "latitud": round(lat, 6),
        "longitud": round(lng, 6),
        "categoria": titulo(a.get("ter_categoria")),
        "horario": titulo(horario),
        "telefono": limpiar(a.get("telefono")),
        "ubigeo": a.get("ubi_id"),
    }


def coords_validas(a):
    lat, lng = coordenada(a.get("latitud")), coordenada(a.get("longitud"))
    return lat is not None and lng is not None and -18.6 < lat < 0.4 and -81.6 < lng < -68.4


def norm(texto):
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes(limpiar(texto).lower())).strip()


def desde_catalogo(crudas):
    """Sin exportación de la web: aproxima la lista pública con las marcas del catálogo."""
    agencias, descartadas = [], []
    for a in crudas:
        nombre = limpiar(a.get("lugar_over") or a.get("nombre"))
        categoria = limpiar(a.get("ter_categoria")).upper()
        motivo = None
        if str(a.get("ter_habilitado_OS")) != "1":
            motivo = "deshabilitada en el sistema"
        elif not coords_validas(a):
            motivo = "sin coordenadas"
        elif categoria in EXCLUIR_CATEGORIA:
            motivo = categoria.lower()
        elif EXCLUIR_NOMBRE.search(nombre):
            motivo = "registro interno"
        if motivo:
            descartadas.append((nombre, motivo))
        else:
            agencias.append(armar(a))
    fuente = "Catálogo de agencias del sistema de Shalom vía https://shalom-api.lat (listado público), filtrado por sus marcas internas."
    return agencias, descartadas, fuente


class ListaAgenciasHTML(HTMLParser):
    """Lee la lista de la pestaña "Agencias" del HTML de shalom.com.pe/agencias."""

    def __init__(self):
        super().__init__()
        self.items, self.actual, self.nivel, self.campo, self.texto = [], None, 0, None, []

    def handle_starttag(self, tag, attrs):
        clases = dict(attrs).get("class") or ""
        if self.actual is None:
            if tag == "div" and "flex flex-row py-4 cursor-pointer" in clases:
                self.actual, self.nivel = {"nombre": "", "direccion": "", "categoria": ""}, 1
            return
        self.nivel += 1
        if tag == "p" and "text-color-description-air" in clases:
            self.campo, self.texto = "nombre", []
        elif tag == "p" and "text-color-description-agen" in clases:
            self.campo, self.texto = "direccion", []
        elif tag == "div" and "text-red-shalom" in clases:
            self.campo, self.texto = "categoria", []

    def handle_endtag(self, tag):
        if self.actual is None:
            return
        if self.campo and tag in ("p", "div"):
            self.actual[self.campo] = limpiar("".join(self.texto))
            self.campo = None
        self.nivel -= 1
        if self.nivel == 0:
            if self.actual["nombre"]:
                self.items.append(self.actual)
            self.actual = None

    def handle_data(self, data):
        if self.campo:
            self.texto.append(data)


def leer_exportacion(ruta):
    texto = Path(ruta).read_text(encoding="utf-8", errors="replace")
    if ruta.lower().endswith((".html", ".htm")) or texto.lstrip().startswith("<"):
        lector = ListaAgenciasHTML()
        lector.feed(texto)
        if not lector.items:
            sys.exit("No se encontró la lista de agencias en el HTML. Copia el outerHTML de <html> con la lista ya cargada.")
        return {"fuente": "lista", "fecha": date.today().isoformat(), "agencias": lector.items}
    return json.loads(texto)


def desde_web(ruta, crudas):
    """Con la página shalom.com.pe/agencias: usa exactamente las agencias que muestra."""
    export = leer_exportacion(ruta)
    por_id = {str(a.get("ter_id")): a for a in crudas}
    agencias, descartadas = [], []

    if export.get("fuente") == "app":
        # Mismo filtro que usa la página para la pestaña "Agencias"
        visibles = [a for a in export["agencias"] if a.get("web") == 1 and a.get("agente") == 0 and a.get("puntospro") == 0]
        for v in visibles:
            if sin_tildes(limpiar(v.get("categoria")).upper()) in EXCLUIR_WEB:
                descartadas.append((limpiar(v.get("nombre")), f"{titulo(v.get('categoria'))} (no es agencia de recojo)"))
                continue
            reg = {
                "ter_id": v.get("ter_id"), "lugar_over": v.get("nombre"), "zona": v.get("zona"),
                "provincia": v.get("provincia"), "departamento": v.get("departamento"), "direccion": v.get("direccion"),
                "latitud": v.get("latitud"), "longitud": v.get("longitud"), "ter_categoria": v.get("categoria"),
                "telefono": v.get("telefono"), "hora_atencion": v.get("hora_atencion"), "hora_domingo": v.get("hora_domingo"),
                "ubi_id": v.get("ubi_id"),
            }
            respaldo = por_id.get(str(v.get("ter_id")))
            if not coords_validas(reg) and respaldo and coords_validas(respaldo):
                reg["latitud"], reg["longitud"] = respaldo["latitud"], respaldo["longitud"]
            if coords_validas(reg):
                agencias.append(armar(reg))
            else:
                descartadas.append((limpiar(v.get("nombre")), "Shalom no publica sus coordenadas"))
        print(f"La página muestra {len(visibles)} agencias (de {export.get('total_catalogo')} en su catálogo).")
    else:
        # Solo nombres y direcciones de la lista visible: se buscan en el catálogo para obtener coordenadas
        por_nombre = {}
        for a in crudas:
            por_nombre.setdefault(norm(a.get("lugar_over")), []).append(a)
        usados = set()
        for v in export["agencias"]:
            if sin_tildes(limpiar(v.get("categoria")).upper()) in EXCLUIR_WEB:
                descartadas.append((limpiar(v.get("nombre")), f"{titulo(v.get('categoria'))} (no es agencia de recojo)"))
                continue
            candidatos = [a for a in por_nombre.get(norm(v.get("nombre")), []) if str(a.get("ter_id")) not in usados]
            if not candidatos:
                descartadas.append((limpiar(v.get("nombre")), "no está en el catálogo"))
                continue
            candidatos.sort(key=lambda a: -SequenceMatcher(None, norm(a.get("direccion")), norm(v.get("direccion"))).ratio())
            elegido = candidatos[0]
            usados.add(str(elegido.get("ter_id")))
            if coords_validas(elegido):
                registro = armar(elegido)
                if v.get("categoria"):
                    registro["categoria"] = titulo(v["categoria"])   # la categoría que muestra la página oficial
                agencias.append(registro)
            else:
                descartadas.append((limpiar(v.get("nombre")), "sin coordenadas en el catálogo"))
        print(f"La página muestra {len(export['agencias'])} agencias.")

    fuente = f"Agencias visibles en https://shalom.com.pe/agencias (exportadas el {limpiar(export.get('fecha'))[:10]})."
    return agencias, descartadas, fuente


def main():
    crudas = descargar_catalogo()
    if len(sys.argv) > 1:
        agencias, descartadas, fuente = desde_web(sys.argv[1], crudas)
    else:
        agencias, descartadas, fuente = desde_catalogo(crudas)

    agencias.sort(key=lambda x: (x["departamento"], x["provincia"], x["distrito"], x["nombre"]))
    doc = {
        "meta": {
            "descripcion": "Agencias Shalom vigentes para el Buscador de Agencias Shalom.",
            "fuente": fuente,
            "fecha_extraccion": date.today().isoformat(),
            "total_agencias": len(agencias),
        },
        "agencias": agencias,
    }
    SALIDA.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    deps = len({a["departamento"] for a in agencias})
    print(f"Listo: {len(agencias)} agencias en {deps} departamentos -> {SALIDA.name}")
    if descartadas:
        print(f"No se pudieron usar {len(descartadas)}:")
        for nombre, motivo in descartadas:
            print(f"  - {nombre}: {motivo}")


if __name__ == "__main__":
    main()
