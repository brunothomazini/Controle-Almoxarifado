from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session
from app.models.models import Item, Categoria, Importacao, StatusItem
from app.config import settings


COLUNAS_OBRIGATORIAS = {"codigo", "nome"}
COLUNAS_OPCIONAIS = {
    "codigo_usp", "descricao", "unidade_medida", "quantidade_minima",
    "quantidade_atual", "quantidade_maxima", "localizacao", "status",
    "categoria", "fabricante", "modelo", "numero_serie", "valor_unitario",
    "observacoes",
}


def detectar_formato(caminho: Path) -> str:
    ext = caminho.suffix.lower()
    if ext in (".xlsx", ".xls"):
        return "excel"
    elif ext == ".csv":
        return "csv"
    elif ext == ".ods":
        return "ods"
    return "unknown"


def ler_planilha(caminho: Path) -> Optional[pd.DataFrame]:
    fmt = detectar_formato(caminho)
    try:
        if fmt == "excel":
            return pd.read_excel(caminho, dtype=str, engine="openpyxl")
        elif fmt == "csv":
            return pd.read_csv(caminho, dtype=str, encoding="utf-8-sig")
        elif fmt == "ods":
            return pd.read_excel(caminho, dtype=str, engine="odf")
        return None
    except Exception:
        return None


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {}
    for col in df.columns:
        col_norm = (
            col.strip().lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("ú", "u")
            .replace(" ", "_")
        )
        if col_norm in COLUNAS_OPCIONAIS or col_norm == "codigo" or col_norm == "nome":
            col_map[col] = col_norm
        elif "cod" in col_norm and "codigo" not in col_map.values():
            col_map[col] = "codigo"
        elif "categ" in col_norm:
            col_map[col] = "categoria"
    return df.rename(columns=col_map)


def importar_planilha(db: Session, caminho_arquivo: Path) -> dict:
    if not caminho_arquivo.exists():
        return {"success": False, "error": "Arquivo nao encontrado"}

    df = ler_planilha(caminho_arquivo)
    if df is None:
        return {"success": False, "error": "Formato de arquivo nao suportado ou corrompido"}

    df = normalizar_colunas(df)
    colunas = set(df.columns)
    if not COLUNAS_OBRIGATORIAS.issubset(colunas):
        faltando = COLUNAS_OBRIGATORIAS - colunas
        return {"success": False, "error": f"Colunas obrigatorias faltando: {faltando}"}

    importacao = Importacao(
        nome_arquivo=caminho_arquivo.name,
        tipo_origem=detectar_formato(caminho_arquivo),
        total_registros=len(df),
    )
    db.add(importacao)
    db.flush()

    importados = 0
    erros = 0
    erros_detalhes = []

    for idx, row in df.iterrows():
        try:
            dados = row.to_dict()
            codigo = str(dados.get("codigo", "")).strip()

            existing = db.query(Item).filter(Item.codigo == codigo).first()
            if existing:
                erros += 1
                erros_detalhes.append(f"Linha {idx+2}: codigo '{codigo}' ja existe")
                continue

            nome_categoria = str(dados.get("categoria", "")).strip()
            categoria_id = None
            if nome_categoria:
                cat = db.query(Categoria).filter(Categoria.nome == nome_categoria).first()
                if not cat:
                    cat = Categoria(nome=nome_categoria)
                    db.add(cat)
                    db.flush()
                categoria_id = cat.id

            status_str = str(dados.get("status", "disponivel")).strip().lower()
            status_valido = StatusItem.DISPONIVEL
            for s in StatusItem:
                if s.value == status_str:
                    status_valido = s
                    break

            item = Item(
                codigo=codigo,
                codigo_usp=str(dados.get("codigo_usp", "")).strip() or None,
                nome=str(dados.get("nome", "")).strip(),
                descricao=str(dados.get("descricao", "")).strip() or None,
                unidade_medida=str(dados.get("unidade_medida", "un")).strip(),
                quantidade_minima=float(dados.get("quantidade_minima", 0) or 0),
                quantidade_atual=float(dados.get("quantidade_atual", 0) or 0),
                quantidade_maxima=float(dados.get("quantidade_maxima", 0) or 0),
                localizacao=str(dados.get("localizacao", "")).strip() or None,
                status=status_valido,
                categoria_id=categoria_id,
                fabricante=str(dados.get("fabricante", "")).strip() or None,
                modelo=str(dados.get("modelo", "")).strip() or None,
                numero_serie=str(dados.get("numero_serie", "")).strip() or None,
                valor_unitario=float(dados.get("valor_unitario", 0) or 0),
                observacoes=str(dados.get("observacoes", "")).strip() or None,
            )
            db.add(item)
            importados += 1
        except Exception as e:
            erros += 1
            erros_detalhes.append(f"Linha {idx+2}: {str(e)}")

    importacao.importados = importados
    importacao.erros = erros
    importacao.detalhes = {"erros_detalhes": erros_detalhes[:100]}
    db.commit()

    return {
        "success": True,
        "importacao_id": importacao.id,
        "total": len(df),
        "importados": importados,
        "erros": erros,
    }


def concatenar_planilhas(db: Session, arquivos: list[Path]) -> dict:
    dfs = []
    total_linhas = 0
    erros_globais = []

    for arquivo in arquivos:
        df = ler_planilha(arquivo)
        if df is None:
            erros_globais.append(f"Erro ao ler {arquivo.name}")
            continue
        df = normalizar_colunas(df)
        df["_origem"] = arquivo.name
        dfs.append(df)
        total_linhas += len(df)

    if not dfs:
        return {"success": False, "error": "Nenhum arquivo valido para concatenar"}

    df_final = pd.concat(dfs, ignore_index=True)
    caminho_temp = settings.DATA_DIR / "concatenado_temp.xlsx"
    df_final.to_excel(caminho_temp, index=False, engine="openpyxl")

    resultado = importar_planilha(db, caminho_temp)
    caminho_temp.unlink(missing_ok=True)

    return {
        "success": True,
        "arquivos_processados": len(dfs),
        "total_linhas": total_linhas,
        "importacao": resultado,
        "erros_globais": erros_globais,
    }
