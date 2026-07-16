import requests, re, json, os

URL = "https://fob.usp.br/estoque-almoxarifado/"
DATA_PATH = "data/almox.json"

def fetch():
    print(f"Baixando dados de {URL}...")
    response = requests.get(URL)
    # Procura pelo JSON no conteúdo da página (ajuste o regex se o site mudar)
    m = re.search(r'\{"total":.*?\}', response.text, re.DOTALL)
    if not m:
        raise Exception("Não foi possível encontrar o JSON na página da FOB")
    
    data = json.loads(m.group(0))
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Sucesso! {len(data['itens'])} itens salvos em {DATA_PATH}")

if __name__ == "__main__":
    fetch()
