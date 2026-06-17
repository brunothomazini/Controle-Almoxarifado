"""
Importa todos os itens do arquivo Catalogo_de_Almoxarifado para o banco.
Classifica como "almoxarifado" (marcador X) ou "padronizado" (marcador E-MAIL).

Uso: python -m app.scripts.importar_catalogo
"""

import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models.models import Categoria, Item, Fornecedor, TipoControle, StatusItem
from app.config import settings

CATALOGO_PATH = Path(__file__).parent.parent.parent.parent / "Catalogo_de_Almoxarifado-itens-padronizados para dashboard.xlsx"

MAPA_SHEETS = {
    "Odontológico": {"descricao": "Materiais odontológicos", "codigo_prefixo": "ODT"},
    "Médico-Hospitalar": {"descricao": "Materiais médico-hospitalares", "codigo_prefixo": "MED"},
    "Papelaria": {"descricao": "Materiais de papelaria e escritório", "codigo_prefixo": "PAP"},
    "Limpeza": {"descricao": "Produtos de limpeza", "codigo_prefixo": "LIM"},
    "Informática": {"descricao": "Equipamentos de informática", "codigo_prefixo": "INF"},
    "Descartáveis Higiene e Limpeza": {"descricao": "Descartáveis de higiene e limpeza", "codigo_prefixo": "DHL"},
    "Descartáveis médico-hospitalar": {"descricao": "Descartáveis médico-hospitalares", "codigo_prefixo": "DMH"},
    "Gêneros alimentícios e copa": {"descricao": "Gêneros alimentícios e copa", "codigo_prefixo": "ALI"},
}


def normalizar_marcador(valor) -> str:
    if pd.isna(valor):
        return "outro"
    v = str(valor).strip().upper()
    if v == "X":
        return "almoxarifado"
    elif v == "E-MAIL":
        return "padronizado"
    return "outro"


def parse_sheet_comum(df: pd.DataFrame, sheet_name: str, col_map: list[str]) -> list[dict]:
    itens = []
    header_idx = None
    for i, row in df.iterrows():
        vals = [str(v).strip().upper() for v in row if str(v).strip() != "nan"]
        if "BEM" in vals:
            header_idx = i
            break
    if header_idx is None:
        return itens

    # Renomear colunas
    df_cols = {}
    row_header = df.iloc[header_idx]
    for j, nome_original in enumerate(row_header.items()):
        idx = nome_original[0]
        nome = str(nome_original[1]).strip().upper() if str(nome_original[1]).strip() != "nan" else ""
        if "BEM" in nome or "CÓDIGO" in nome or "CODIGO" in nome or nome.isdigit():
            df_cols[idx] = "codigo"
        elif "FORNECEDOR" in nome:
            df_cols[idx] = "fornecedor"
        elif "MARCA" in nome:
            df_cols[idx] = "marca"
        elif "MODELO" in nome:
            df_cols[idx] = "modelo"
        elif "ALMOX" in nome or nome == "ALMOXARIFADO" or "REQUISI" in nome:
            df_cols[idx] = "marcador"

    # Coluna sem nome entre MARCA/MODELO e ALMOX é a descrição
    known = list(df_cols.keys())
    if known:
        last_known_idx = max(known)
        # Procurar colunas sem mapeamento entre o último conhecido e o marcador
        marcador_col = None
        for k, v in df_cols.items():
            if v == "marcador":
                marcador_col = k
                break
        if marcador_col:
            # Coluna entre último conhecido (exceto marcador) e marcador
            cols_before_marker = [c for c in df.columns if c not in df_cols or df_cols.get(c) == "marcador" or True]
            for c in df.columns:
                if c not in df_cols:
                    df_cols[c] = "descricao"
                    break
            # Se ainda não achou e tem coluna vazia antes do marcador
            if "descricao" not in df_cols.values():
                for c in df.columns:
                    if c < marcador_col and c not in [k for k, v in df_cols.items() if v != "marcador"]:
                        df_cols[c] = "descricao"
                        break

    # Se marcador não encontrado, última coluna é marcador
    if "marcador" not in df_cols.values():
        for j, nome_original in enumerate(row_header.items()):
            if str(nome_original[1]).strip() in ("nan", "") or j == len(df.columns) - 1:
                if "marcador" not in [v for v in df_cols.values()]:
                    df_cols[nome_original[0]] = "marcador"

    # Se descricao ainda não mapeada, pegar a maior coluna não mapeada
    if "descricao" not in df_cols.values():
        for c in df.columns:
            if c not in df_cols:
                df_cols[c] = "descricao"
                break

    data_rows = df.iloc[header_idx + 1:]
    data_rows = data_rows.dropna(how="all")

    for _, row in data_rows.iterrows():
        codigo_raw = str(row.get([k for k, v in df_cols.items() if v == "codigo"][0])) if [k for k, v in df_cols.items() if v == "codigo"] else ""
        codigo = codigo_raw.strip().upper()
        if codigo in ("", "NAN", "XXXX", "0", "0.0"):
            continue

        desc_col = [k for k, v in df_cols.items() if v == "descricao"]
        descricao = str(row.get(desc_col[0])).strip() if desc_col else ""
        if descricao == "nan":
            descricao = ""

        forn_key = [k for k, v in df_cols.items() if v == "fornecedor"]
        fornecedor = str(row.get(forn_key[0])).strip() if forn_key else ""
        if fornecedor == "nan":
            fornecedor = ""

        marca_key = [k for k, v in df_cols.items() if v == "marca"]
        marca = str(row.get(marca_key[0])).strip() if marca_key else ""
        if marca == "nan":
            marca = ""

        modelo_key = [k for k, v in df_cols.items() if v == "modelo"]
        modelo = str(row.get(modelo_key[0])).strip() if modelo_key else ""
        if modelo == "nan":
            modelo = ""

        marc_key = [k for k, v in df_cols.items() if v == "marcador"]
        marcador_val = row.get(marc_key[0]) if marc_key else None
        tipo = normalizar_marcador(marcador_val)

        itens.append({
            "codigo": codigo if codigo and codigo != "NAN" else None,
            "nome": (descricao[:297] + "...") if len(descricao) > 300 else descricao,
            "descricao": descricao,
            "fornecedor": fornecedor,
            "marca": marca,
            "modelo": modelo,
            "tipo_controle": tipo,
            "sheet_name": sheet_name,
        })

    return itens


def parse_sheet_informatica(df: pd.DataFrame) -> list[dict]:
    itens = []
    header_found = False
    codigo_col = None
    desc_col = None

    for i, row in df.iterrows():
        vals = [str(v).strip().upper() for v in row if str(v).strip() != "nan"]
        for v in vals:
            if "CÓDIGO" in v or "CODIGO" in v:
                header_found = True
                for j, val in enumerate(row):
                    sval = str(val).strip().upper() if str(val).strip() != "nan" else ""
                    if "CÓDIGO" in sval or "CODIGO" in sval:
                        codigo_col = j
                    elif "DESCRI" in sval or "DESCRIÇÃO" in sval:
                        desc_col = j
                break
        if header_found:
            break

    if not header_found:
        # Fallback: sheet Informatica starts at row 1
        codigo_col = 0
        desc_col = 1

    for i, row in df.iterrows():
        if i <= 1 and header_found:
            continue
        codigo = str(row.iloc[codigo_col]).strip() if codigo_col is not None else ""
        if codigo in ("", "nan", "Código do Bem"):
            continue
        descricao = str(row.iloc[desc_col]).strip() if desc_col is not None else ""
        if descricao in ("", "nan"):
            continue

        itens.append({
            "codigo": codigo,
            "nome": (descricao[:297] + "...") if len(descricao) > 300 else descricao,
            "descricao": descricao,
            "fornecedor": "",
            "marca": "",
            "modelo": "",
            "tipo_controle": "outro",
            "sheet_name": "Informática",
        })

    return itens


def importar():
    if not CATALOGO_PATH.exists():
        print(f"ERRO: Arquivo nao encontrado: {CATALOGO_PATH}")
        return

    init_db()
    db = SessionLocal()

    total_importados = 0
    total_ignorados = 0
    total_erros = 0

    xls = pd.ExcelFile(CATALOGO_PATH, engine="openpyxl")

    for sheet_name in xls.sheet_names:
        info = MAPA_SHEETS.get(sheet_name, {"descricao": "", "codigo_prefixo": "OUT"})
        print(f"\nProcessando: {sheet_name}...")

        df = pd.read_excel(CATALOGO_PATH, sheet_name=sheet_name, engine="openpyxl", header=None)

        if sheet_name == "Informática":
            dados = parse_sheet_informatica(df)
        else:
            dados = parse_sheet_comum(df, sheet_name, [])

        print(f"  Itens extraidos: {len(dados)}")

        if not dados:
            continue

        # Criar ou obter categoria
        nome_cat = sheet_name.strip()
        cat = db.query(Categoria).filter(Categoria.nome == nome_cat).first()
        if not cat:
            cat = Categoria(nome=nome_cat, descricao=info["descricao"])
            db.add(cat)
            db.flush()

        for item_data in dados:
            try:
                codigo = item_data["codigo"]
                if not codigo:
                    total_ignorados += 1
                    continue

                # Verificar se ja existe
                existente = db.query(Item).filter(Item.codigo == codigo).first()
                if existente:
                    total_ignorados += 1
                    continue

                # Criar ou obter fornecedor
                fornecedor_id = None
                nome_forn = item_data["fornecedor"].strip()
                if nome_forn and nome_forn != "nan":
                    forn = db.query(Fornecedor).filter(Fornecedor.nome == nome_forn).first()
                    if not forn:
                        forn = Fornecedor(nome=nome_forn)
                        db.add(forn)
                        db.flush()
                    fornecedor_id = forn.id

                # Determinar tipo de controle
                tipo_map = {
                    "almoxarifado": TipoControle.ALMOXARIFADO,
                    "padronizado": TipoControle.PADRONIZADO,
                    "outro": TipoControle.OUTRO,
                }
                tipo_controle = tipo_map.get(item_data["tipo_controle"], TipoControle.OUTRO)

                item = Item(
                    codigo=codigo,
                    nome=item_data["nome"][:300],
                    descricao=item_data["descricao"],
                    fabricante=item_data["marca"] or None,
                    modelo=item_data["modelo"] or None,
                    fornecedor_id=fornecedor_id,
                    tipo_controle=tipo_controle,
                    categoria_id=cat.id,
                    status=StatusItem.DISPONIVEL,
                )
                db.add(item)
                total_importados += 1

            except Exception as e:
                total_erros += 1
                print(f"  ERRO ao importar item {item_data.get('codigo', '?')}: {e}")

        db.commit()

    db.close()
    print(f"\n=== RESUMO ===")
    print(f"Importados: {total_importados}")
    print(f"Ignorados (ja existentes/sem codigo): {total_ignorados}")
    print(f"Erros: {total_erros}")
    print(f"Total processados: {total_importados + total_ignorados + total_erros}")


if __name__ == "__main__":
    importar()
