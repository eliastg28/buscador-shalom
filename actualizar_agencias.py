#!/usr/bin/env python3
"""
Actualiza agencias_shalom.json con el catálogo vigente de agencias Shalom.

Fuente: listado público de shalom-api.lat (https://shalom-api.lat/docs/agencias), que replica
el catálogo del sistema de Shalom (el mismo que muestra https://shalom.com.pe/agencias) y lo
refresca cada 3 horas. Es un endpoint de demostración sin API key: úsalo solo para actualizar
esta base de vez en cuando, no en cada visita a la app.

Uso (no requiere instalar nada):
    python actualizar_agencias.py
"""
import json
import re
import sys
import unicodedata
import urllib.request
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


def main():
    print(f"Descargando {URL} ...")
    req = urllib.request.Request(URL, headers={"Accept": "application/json", "User-Agent": "buscador-agencias-shalom/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        datos = json.load(resp)
    crudas = datos.get("data") or []
    if not crudas:
        sys.exit("La respuesta no trae agencias; no se modificó agencias_shalom.json")

    agencias, descartadas = [], []
    for a in crudas:
        lat, lng = coordenada(a.get("latitud")), coordenada(a.get("longitud"))
        nombre = limpiar(a.get("lugar_over") or a.get("nombre"))
        categoria = limpiar(a.get("ter_categoria")).upper()
        motivo = None
        if str(a.get("ter_habilitado_OS")) != "1":
            motivo = "deshabilitada en el sistema"
        elif lat is None or lng is None or not (-18.6 < lat < 0.4 and -81.6 < lng < -68.4):
            motivo = "sin coordenadas"
        elif categoria in EXCLUIR_CATEGORIA:
            motivo = categoria.lower()
        elif EXCLUIR_NOMBRE.search(nombre):
            motivo = "registro interno"
        if motivo:
            descartadas.append((nombre, motivo))
            continue

        direccion, referencia = separar_referencia(a.get("direccion"))
        dep = DEPARTAMENTOS.get(sin_tildes(limpiar(a.get("departamento")).upper()), titulo(a.get("departamento")))
        horario = limpiar(a.get("hora_atencion"))
        if limpiar(a.get("hora_domingo")):
            horario += f" | Domingo: {limpiar(a.get('hora_domingo'))}"
        agencias.append({
            "id": f"SH-{a.get('ter_id')}",
            "nombre": titulo(nombre),
            "departamento": dep,
            "provincia": titulo(a.get("provincia")),
            "distrito": titulo(a.get("zona")),
            "direccion": titulo(direccion),
            "referencia": titulo(referencia),
            "latitud": round(lat, 6),
            "longitud": round(lng, 6),
            "categoria": titulo(categoria),
            "horario": titulo(horario),
            "telefono": limpiar(a.get("telefono")),
            "ubigeo": a.get("ubi_id"),
        })

    agencias.sort(key=lambda x: (x["departamento"], x["provincia"], x["distrito"], x["nombre"]))
    doc = {
        "meta": {
            "descripcion": "Agencias Shalom vigentes para el Buscador de Agencias Shalom.",
            "fuente": "Catálogo de agencias del sistema de Shalom vía https://shalom-api.lat (listado público).",
            "fecha_extraccion": date.today().isoformat(),
            "total_agencias": len(agencias),
            "excluidas": "Puntos PRO, agencias solo de envío, aeropuertos, almacenes, registros internos y deshabilitadas.",
        },
        "agencias": agencias,
    }
    SALIDA.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    deps = len({a["departamento"] for a in agencias})
    print(f"Listo: {len(agencias)} agencias en {deps} departamentos -> {SALIDA.name}")
    print(f"Descartadas: {len(descartadas)} (de {len(crudas)} registros del catálogo)")


if __name__ == "__main__":
    main()
