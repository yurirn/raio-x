from openpyxl import Workbook

from scripts.import_spl import rows_from_workbook, store_login


def test_importer_skips_header_and_exact_duplicate_rows(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Nome", "Filial for BI", "COORD", "GERENTE"])
    sheet.append(["WILLIAN", "DN - LOJA SHOP. PAULISTA - COMM", "EDNA", "SERGIO"])
    sheet.append(["WILLIAN", "DN - LOJA SHOP. PAULISTA - COMM", "EDNA", "SERGIO"])
    path = tmp_path / "sergio.xlsx"
    workbook.save(path)

    rows, duplicates = rows_from_workbook(path)

    assert rows == [("WILLIAN", "DN - LOJA SHOP. PAULISTA - COMM", "EDNA")]
    assert duplicates == 1
    assert store_login("83 - SHOP LIGHT - COMM") == "shoplight"
