import sqlite3
import sys
from pathlib import Path


CONSULTA = """
SELECT bom.parent_item, item.Description, item.cost, bom.ITEM_TYPE,
       SUM(bom.quantity) AS Cantidad
FROM bom
INNER JOIN Item ON bom.PARENT_ITEM = item.Item_Code
WHERE bom.ITEM_TYPE = 'P' AND bom.PARENT_ITEM = ?
GROUP BY bom.parent_item, item.Description, item.cost, bom.ITEM_TYPE
"""


def main():
    codigo = input("Teclea el parent_item: ").strip()
    if not codigo:
        print("Error: debes proporcionar un parent_item.", file=sys.stderr)
        return 1

    database = Path(__file__).resolve().parent / "DatosExamenCopia.db"
    try:
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as conexion:
            resultados = conexion.execute(CONSULTA, (codigo,)).fetchall()
    except sqlite3.Error as error:
        print(f"Error al consultar la base de datos: {error}", file=sys.stderr)
        return 1

    if not resultados:
        print(f"No se encontraron resultados para parent_item: {codigo}")
        return 0

    for parent_item, descripcion, costo, tipo, cantidad in resultados:
        print(f"Parent item: {parent_item}")
        print(f"Descripcion: {descripcion}")
        print(f"Costo: {costo}")
        print(f"Tipo: {tipo}")
        print(f"Cantidad: {cantidad}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
