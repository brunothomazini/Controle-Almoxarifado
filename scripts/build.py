import json, sys, os

HTML_PATH = "frontend/index.html"
JSON_PATH = "data/almox.json"

def main():
    if not os.path.exists(JSON_PATH):
        print("ERRO: data/almox.json nao encontrado. Execute fetch.py primeiro (se o API estiver disponivel).")
        sys.exit(1)

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    json_str = json.dumps(data, ensure_ascii=False)

    marker_start = 'const DADOS = '
    marker_end = ';\n        let paginaAtual'

    start_idx = html.find(marker_start)
    end_idx = html.find(marker_end, start_idx)

    if start_idx == -1 or end_idx == -1:
        print("ERRO: nao foi possivel encontrar o marcador DADOS no HTML")
        sys.exit(1)

    new_html = html[:start_idx] + marker_start + json_str + marker_end + html[end_idx:]

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_html)

    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"OK! {len(data['itens'])} itens embutidos em frontend/index.html e index.html")

if __name__ == "__main__":
    main()
