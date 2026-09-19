from pathlib import Path
import csv


DATA_FILE = Path("/app/data/iss_sample.csv")


def search_iss(
    municipio: str | None = None,
    uf: str | None = None,
    codigo: str | None = None,
):
    if not DATA_FILE.exists():
        return []

    results = []

    with DATA_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:

            if (
                municipio
                and municipio.lower()
                not in row["municipio"].lower()
            ):
                continue

            if (
                uf
                and uf.upper()
                != row["uf"].upper()
            ):
                continue

            if (
                codigo
                and codigo.lower()
                not in row["codigo_servico"].lower()
            ):
                continue

            results.append(row)

    return results