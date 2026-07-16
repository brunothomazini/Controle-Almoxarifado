import json, sys, os

DATA_PATH = "data/almox.json"

def main():
    if not os.path.exists(DATA_PATH):
        print("ATENCAO: O API do Mercúrio foi descontinuado pela FOB.")
        print("Nao e possivel obter novos dados automaticamente.")
        print("Para atualizar, coloque o JSON manualmente em data/almox.json")
        print("e execute: python scripts/build.py")
        sys.exit(1)

    print(f"Dados existentes encontrados em {DATA_PATH}")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total: {len(data['itens'])} itens")

if __name__ == "__main__":
    main()
