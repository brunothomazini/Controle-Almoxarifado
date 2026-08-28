"""
Importa o arquivo relatorioRegistroPreco.csv para o banco de dados.
Cruza os itens pelo campo 'Bem' (codigo) e atualiza:
- numero_compra, fornecedor, fabricante, modelo, preco_referencial, preco_final
- Marca como 'baixado' itens que existem no banco mas NAO estao no CSV.

Uso: python -m app.scripts.importar_registro_preco [caminho_do_csv]

Se nenhum caminho for informado, busca por 'relatorioRegistroPreco.csv' na raiz do projeto.
"""

import csv
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal, init_db
from app.models.models import Item, Fornecedor, StatusItem

DEFAULT_CSV = Path(__file__).parent.parent.parent.parent / "relatorioRegistroPreco.csv"


def parse_float_br(valor: str) -> float:
    """Converte string brasileira (1.234,56) para float."""
    if not valor:
        return 0.0
    v = valor.strip().replace(".", "").replace(",", ".")
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def importar_registro_preco(caminho_csv: str = None) -> dict:
    """
    Importa o CSV de registro de precos e cruza com itens do banco.
    
    Returns:
        dict com estatisticas: atualizados, criados_fornecedor, baixados, erros
    """
    if caminho_csv is None:
        caminho_csv = str(DEFAULT_CSV)
    
    csv_path = Path(caminho_csv)
    if not csv_path.exists():
        return {"erro": f"Arquivo nao encontrado: {csv_path}"}
    
    init_db()
    db = SessionLocal()
    
    stats = {
        "atualizados": 0,
        "itens_nao_encontrados_csv": 0,
        "fornecedores_criados": 0,
        "fornecedores_atualizados": 0,
        "itens_baixados": 0,
        "erros": 0,
        "itens_processados": 0,
    }
    
    # 1. Ler o CSV
    registros_csv = {}
    try:
        with open(csv_path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                bem = row.get("Bem", "").strip()
                if not bem:
                    continue
                
                # Chave: codigo do bem
                # Guarda o ultimo registro para este bem (pode haver duplicatas)
                registros_csv[bem] = {
                    "compra": row.get("Compra", "").strip(),
                    "participante": row.get("Participante", "").strip(),
                    "gerenciadora": row.get("Gerenciadora", "").strip(),
                    "marca": row.get("Marca", "").strip(),
                    "modelo": row.get("Modelo", "").strip(),
                    "preco_referencial": parse_float_br(row.get("Preco Referencial", "0")),
                    "preco_final": parse_float_br(row.get("Preco Final", "0")),
                    "total": parse_float_br(row.get("Total", "0")),
                    "restante": parse_float_br(row.get("Restante", "0")),
                    "situacao": row.get("Situacao", "").strip(),
                    "grupo": row.get("Grupo", "").strip(),
                    "classe": row.get("Classe", "").strip(),
                }
    except Exception as e:
        db.close()
        return {"erro": f"Erro ao ler CSV: {str(e)}"}
    
    print(f"CSV carregado: {len(registros_csv)} itens unicos (Bem)")
    
    # 2. Buscar todos os itens do banco
    todos_itens = db.query(Item).all()
    itens_por_codigo = {item.codigo: item for item in todos_itens}
    print(f"Itens no banco: {len(itens_por_codigo)}")
    
    # 3. Cruzar: atualizar itens que estao no CSV
    codigos_banco = set(itens_por_codigo.keys())
    codigos_csv = set(registros_csv.keys())
    codigos_em_ambos = codigos_banco & codigos_csv
    codigos_so_banco = codigos_banco - codigos_csv
    
    print(f"Codigos em ambos (banco + CSV): {len(codigos_em_ambos)}")
    print(f"Codigos so no banco (serao baixados): {len(codigos_so_banco)}")
    
    # 4. Atualizar itens que estao no CSV
    for codigo in codigos_em_ambos:
        try:
            reg = registros_csv[codigo]
            item = itens_por_codigo[codigo]
            
            # Atualizar numero_compra
            if reg["compra"]:
                item.numero_compra = reg["compra"]
            
            # Atualizar fornecedor
            nome_forn = reg["participante"] or reg["gerenciadora"]
            if nome_forn and nome_forn != "nan":
                forn = db.query(Fornecedor).filter(Fornecedor.nome == nome_forn).first()
                if not forn:
                    forn = Fornecedor(nome=nome_forn)
                    db.add(forn)
                    db.flush()
                    stats["fornecedores_criados"] += 1
                else:
                    stats["fornecedores_atualizados"] += 1
                item.fornecedor_id = forn.id
            
            # Atualizar marca/modelo
            if reg["marca"]:
                item.fabricante = reg["marca"]
            if reg["modelo"]:
                item.modelo = reg["modelo"]
            
            # Atualizar precos
            if reg["preco_referencial"] > 0:
                item.preco_referencial = reg["preco_referencial"]
            if reg["preco_final"] > 0:
                item.preco_final = reg["preco_final"]
                item.valor_unitario = reg["preco_final"]
            
            # Atualizar status baseado na situacao do CSV
            if reg["situacao"].upper() == "VIGENTE":
                item.status = StatusItem.DISPONIVEL
            elif reg["situacao"].upper() in ("INDISPONIVEL", "CANCELADO", "SUSPENSO"):
                item.status = StatusItem.BAIXADO
            
            stats["atualizados"] += 1
        except Exception as e:
            stats["erros"] += 1
            print(f"  ERRO ao atualizar item {codigo}: {e}")
    
    # 5. Marcar itens que so estao no banco (nao encontrados no CSV) como baixados
    for codigo in codigos_so_banco:
        try:
            item = itens_por_codigo[codigo]
            if item.status != StatusItem.BAIXADO:
                item.status = StatusItem.BAIXADO
                stats["itens_baixados"] += 1
        except Exception as e:
            stats["erros"] += 1
            print(f"  ERRO ao baixar item {codigo}: {e}")
    
    stats["itens_nao_encontrados_csv"] = len(codigos_so_banco)
    stats["itens_processados"] = len(todos_itens)
    
    # 6. Commit
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        stats["erros"] += 1
        return {"erro": f"Erro ao salvar no banco: {str(e)}", "stats": stats}
    finally:
        db.close()
    
    return stats


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else None
    resultado = importar_registro_preco(caminho)
    
    print("\n=== RESUMO DA IMPORTACAO ===")
    if "erro" in resultado:
        print(f"ERRO: {resultado['erro']}")
    else:
        print(f"Itens processados:     {resultado['itens_processados']}")
        print(f"Itens atualizados:     {resultado['atualizados']}")
        print(f"Fornecedores criados:  {resultado['fornecedores_criados']}")
        print(f"Fornecedores atualizados: {resultado['fornecedores_atualizados']}")
        print(f"Itens baixados (sem CSV): {resultado['itens_baixados']}")
        print(f"Erros:                 {resultado['erros']}")
