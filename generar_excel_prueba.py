#!/usr/bin/env python3
"""
Genera clientes_prueba_peru.xlsx con clientes de prueba de distintos departamentos del Perú,
usando exactamente las mismas columnas del formulario de la tienda.

Requisitos:
    pip install pandas openpyxl

Uso:
    python generar_excel_prueba.py                 # crea clientes_prueba_peru.xlsx junto a este script
    python generar_excel_prueba.py otra_ruta.xlsx  # crea el archivo en la ruta indicada

Los nombres y números de WhatsApp son ficticios. Las direcciones son calles reales
para que la búsqueda de coordenadas funcione de verdad.
"""
import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLUMNAS = [
    "Nombres y Apellidos",
    "WhatsApp",
    "Departamento",
    "Ciudad y/o Distrito",
    "Dirección Completa",
    "Referencia de dirección",
]

# Cada fila sigue el orden de COLUMNAS.
CLIENTES = [
    ["Lucía Fernández Rojas", "+51 900 100 201", "La Libertad", "Trujillo", "Jr. Pizarro 412", "A media cuadra de la Plaza de Armas"],
    ["Carlos Mendoza Quispe", "900 100 202", "Lima", "Miraflores", "Av. José Larco 345", "Frente al Parque Kennedy"],
    ["Rosa Huamán Torres", "900100203", "Lima", "San Juan de Lurigancho", "Av. Próceres de la Independencia 1632", "Cerca a la estación Los Jardines"],
    ["Jorge Salazar Paredes", "900-100-204", "Arequipa", "Arequipa", "Calle Mercaderes 212", "A una cuadra de la Plaza de Armas"],
    ["María Chávez Ramírez", "900 100 205", "Piura", "Piura", "Av. Grau 1150", "Frente al parque"],
    ["Luis Condori Mamani", "900 100 206", "Cusco", "Wanchaq", "Av. de la Cultura 1020", "Cerca al Hospital Regional"],
    ["Ana Rojas Vilca", "900 100 207", "Junín", "Huancayo", "Calle Real 789", "Frente a la Plaza Huamanmarca"],
    ["Pedro Castillo Díaz", "900 100 208", "Lambayeque", "Chiclayo", "Av. José Balta 1050", "A dos cuadras del Mercado Modelo"],
    ["Sofía Vargas León", "900 100 209", "Callao", "Callao", "Av. Sáenz Peña 350", "Cerca a la Plaza Grau"],
    ["Miguel Ángel Flores Ríos", "900 100 210", "Ica", "Ica", "Av. San Martín 755", "A dos cuadras de la Plaza de Armas"],
    ["Carmen Gutiérrez Silva", "900 100 211", "Áncash", "Chimbote", "Av. José Pardo 835", "Frente a la Plaza de Armas de Chimbote"],
    ["Diego Ramírez Tello", "900 100 212", "Loreto", "Iquitos", "Jr. Próspero 450", "Cerca a la Plaza de Armas"],
    # Caso difícil a propósito: abreviatura de distrito, Mz/Lt y referencia vaga
    ["Elena Torres Campos", "900 100 213", "Lima", "SJL", "Mz. F Lt. 12 Urb. Canto Rey", "frente al parque"],
]


def generar(salida: Path) -> pd.DataFrame:
    df = pd.DataFrame(CLIENTES, columns=COLUMNAS).astype(str)

    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Clientes")
        ws = writer.sheets["Clientes"]

        encabezado_fill = PatternFill("solid", fgColor="1F5FBF")
        for celda in ws[1]:
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = encabezado_fill
            celda.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 30

        for idx, columna in enumerate(COLUMNAS, start=1):
            ancho = max(len(columna), *(len(str(v)) for v in df[columna])) + 2
            ws.column_dimensions[get_column_letter(idx)].width = min(ancho, 60)

        # WhatsApp como texto para que Excel no lo convierta en número
        for celda in ws["B"][1:]:
            celda.number_format = "@"

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    return df


def main() -> None:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("clientes_prueba_peru.xlsx")
    df = generar(salida)
    print(f"Archivo generado: {salida.resolve()}")
    print(f"{len(df)} clientes en {df['Departamento'].nunique()} departamentos:")
    for depto, total in df["Departamento"].value_counts().sort_index().items():
        print(f"  - {depto}: {total}")


if __name__ == "__main__":
    main()
