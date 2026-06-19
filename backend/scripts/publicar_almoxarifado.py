#!/usr/bin/env python3
import argparse, json, os, sqlite3, sys, xmlrpc.client
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "almoxarifado.db"
TEMPLATE_PATH = Path(__file__).parent / "html_template.txt"
WP_URL = "https://fob.usp.br"
WP_USER = "brubiro"
WP_SLUG = "estoque-almoxarifado"
WP_TITLE = "Consulta Almoxarifado"


def extrair_dados():
    if not DB_PATH.exists():
        print(f"[ERRO] Banco nao encontrado: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
    categorias = [{"id": r["id"], "nome": r["nome"]} for r in cur.fetchall()]
    cat_map = {c["id"]: c["nome"] for c in categorias}
    cur.execute(
        "SELECT i.codigo,i.nome,i.nome_comercial,i.fabricante,i.categoria_id,"
        "i.quantidade_atual,i.unidade_medida,i.solicitar_por_email,"
        "i.tipo_controle,i.status FROM itens i ORDER BY i.nome"
    )
    itens = []
    for r in cur.fetchall():
        row = dict(r)
        cat_nome = cat_map.get(row["categoria_id"], "N/A")
        tc = (row["tipo_controle"] or "").lower()
        if cat_nome == "Informatica":
            pedidos_info = "solicitar para o setor de Informatica"
        elif tc == "almoxarifado":
            pedidos_info = "Almox"
        elif row["solicitar_por_email"]:
            pedidos_info = "e-mail padronizados@fob.usp.br"
        else:
            pedidos_info = "Almox"
        itens.append({
            "codigo": row["codigo"],
            "nome": row["nome"],
            "nome_comercial": row["nome_comercial"] or "-",
            "fabricante": row["fabricante"] or "-",
            "categoria": cat_nome,
            "quantidade_disponivel": row["quantidade_atual"] or 0,
            "unidade": row["unidade_medida"] or "un",
            "status": (row["status"] or "DISPONIVEL").lower(),
            "pedidos_info": pedidos_info,
        })
    conn.close()
    total = len(itens)
    disp = sum(1 for i in itens if i["status"] == "disponivel")
    print(f"[OK] Extraidos: {total} itens, {len(categorias)} categorias "
          f"({disp} disp, {total - disp} indisp)")
    return {
        "total": total,
        "total_categorias": len(categorias),
        "total_disponiveis": disp,
        "total_indisponiveis": total - disp,
        "categorias": [c["nome"] for c in categorias],
        "itens": itens,
    }


def generate_html(dados):
    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    cat_options = "\n".join(
        f"<option value=\"{c}\">{c}</option>"
        for c in dados["categorias"]
    )
    data_json = json.dumps(dados, ensure_ascii=False)
    ultima_data = datetime.now().strftime("%d/%m/%Y")
    stats = (
        f"<div class=\"stat-card\"><div class=\"number\">"
        f"{dados['total']}</div><div class=\"label\">Itens no Estoque</div></div>\n"
        f"<div class=\"stat-card\"><div class=\"number\">"
        f"{dados['total_categorias']}</div><div class=\"label\">Categorias</div></div>\n"
        f"<div class=\"stat-card green\"><div class=\"number\">"
        f"{dados['total_disponiveis']}</div><div class=\"label\">Disponiveis</div></div>\n"
        f"<div class=\"stat-card red\"><div class=\"number\">"
        f"{dados['total_indisponiveis']}</div><div class=\"label\">Indisponiveis / Baixados</div></div>"
    )
    html = html.replace("__WP_TITLE__", WP_TITLE)
    html = html.replace("__DATA_JSON__", data_json)
    html = html.replace("__CAT_OPTIONS__", cat_options)
    html = html.replace("__ULTIMA_DATA__", ultima_data)
    html = html.replace("__STATS_HTML__", stats)
    return html


def upload_arquivo(server, blog_id, wp_user, wp_pass, html_content, filename):
    """Envia o HTML como arquivo na biblioteca de midia do WordPress."""
    import base64
    bits = base64.b64encode(html_content.encode("utf-8")).decode("ascii")
    # Tenta .htm e .html
    extensoes = [
        ("htm", "text/html"),
        ("html", "text/html"),
    ]
    for ext, mime in extensoes:
        nome = f"almoxarifado-consulta.{ext}"
        data = {
            "name": nome,
            "type": mime,
            "bits": bits,
            "overwrite": True,
        }
        try:
            result = server.wp.uploadFile(blog_id, wp_user, wp_pass, data)
            url = result.get("url", "")
            print(f"[OK] Arquivo enviado: {url}")
            return url
        except Exception as e:
            msg = str(e)
            print(f"[..] {ext} falhou ({msg[:80]}...)")
    # Se todas falharem, tenta via metaWeblog.newMediaObject
    try:
        data = {
            "name": "almoxarifado-consulta.html",
            "type": "text/html",
            "bits": base64.b64encode(html_content.encode("utf-8")).decode("ascii"),
            "overwrite": True,
        }
        result = server.metaWeblog.newMediaObject(blog_id, wp_user, wp_pass, data)
        url = result.get("url", "")
        print(f"[OK] Arquivo enviado (metaWeblog): {url}")
        return url
    except Exception as e:
        print(f"[AVISO] metaWeblog falhou: {str(e)[:80]}...")
    return None


def criar_pagina_html(server, blog_id, wp_user, wp_pass, html_content, slug, title):
    """Cria/atualiza pagina com o HTML completo embutido no bloco classico."""
    page_content = (
        f"<!-- wp:freeform -->\n"
        f"{html_content}\n"
        f"<!-- /wp:freeform -->"
    )
    return atualizar_conteudo_pagina(server, blog_id, wp_user, wp_pass,
                                      page_content, slug, title)


def criar_pagina_iframe(server, blog_id, wp_user, wp_pass, file_url, slug, title):
    """Cria/atualiza pagina com iframe apontando pro arquivo estatico."""
    page_content = (
        f"<!-- wp:html -->\n"
        f"<div style=\"width:100%;height:100vh;overflow:hidden;\">\n"
        f"  <iframe src=\"{file_url}\" style=\"width:100%;height:100vh;"
        f"border:none;overflow:auto;\" title=\"{title}\"></iframe>\n"
        f"</div>\n"
        f"<!-- /wp:html -->"
    )
    return atualizar_conteudo_pagina(server, blog_id, wp_user, wp_pass,
                                      page_content, slug, title)


def atualizar_conteudo_pagina(server, blog_id, wp_user, wp_pass,
                               page_content, slug, title):
    """Busca pagina pelo slug e atualiza seu conteudo."""
    existing_page_id = None
    try:
        pages = server.wp.getPosts(blog_id, wp_user, wp_pass, {
            "post_type": "page",
            "number": 100,
            "post_status": "any",
        })
        for pg in pages:
            if pg.get("post_name") == slug:
                existing_page_id = pg["post_id"]
                link = pg.get("link", "")
                print(f"[OK] Pagina existente: ID {existing_page_id} ({link})")
                break
    except Exception as e:
        print(f"[AVISO] Nao foi possivel buscar paginas: {e}")

    if existing_page_id:
        result = server.wp.editPost(blog_id, wp_user, wp_pass,
                                     existing_page_id, {
                                         "post_title": title,
                                         "post_content": page_content,
                                         "post_status": "publish",
                                     })
        if result:
            print(f"[OK] Pagina ATUALIZADA")
            return True
        print("[ERRO] Falha ao atualizar pagina")
        return False
    else:
        page_id = server.wp.newPost(blog_id, wp_user, wp_pass, {
            "post_title": title,
            "post_content": page_content,
            "post_type": "page",
            "post_status": "publish",
            "post_name": slug,
        })
        print(f"[OK] Pagina CRIADA (ID: {page_id})")
        return True


def publicar_wordpress(html_content, wp_url, wp_user, wp_pass, slug, title):
    xmlrpc_url = wp_url.rstrip("/") + "/xmlrpc.php"
    print(f"[..] Conectando em {xmlrpc_url} ...")
    server = xmlrpc.client.ServerProxy(xmlrpc_url)
    try:
        blogs = server.wp.getUsersBlogs(wp_user, wp_pass)
        blog_id = blogs[0]["blogid"]
        print(f"[OK] Conectado - Blog ID: {blog_id}")
    except Exception as e:
        print(f"[ERRO] Falha na autenticacao: {e}")
        sys.exit(1)

    # Tenta 1: Upload do .html como arquivo estatico + iframe na pagina
    print(f"[..] Tentando upload do arquivo estatico...")
    file_url = upload_arquivo(server, blog_id, wp_user, wp_pass,
                               html_content, "almoxarifado-consulta.html")

    if file_url:
        print(f"[..] Criando pagina com iframe...")
        ok = criar_pagina_iframe(server, blog_id, wp_user, wp_pass,
                                  file_url, slug, title)
        if ok:
            print(f"[OK] Pagina: {wp_url.rstrip('/')}/{slug}/")
            return

    # Tenta 2: Se upload falhou, coloca o HTML direto no bloco classico
    print(f"[..] Upload de arquivo nao disponivel. "
          f"Inserindo HTML no bloco classico...")
    ok = criar_pagina_html(server, blog_id, wp_user, wp_pass,
                            html_content, slug, title)
    if ok:
        print(f"[OK] Pagina: {wp_url.rstrip('/')}/{slug}/")
        print(f"[AVISO] WordPress pode remover estilos e scripts do conteudo.")
        print(f"        Se a pagina nao renderizar corretamente, contate a STI")
        print(f"        para liberar upload de arquivos .html no WordPress.")
    else:
        print("[ERRO] Todas as tentativas de publicacao falharam.")
        sys.exit(1)

    # 3. Buscar ou criar pagina
    existing_page_id = None
    try:
        pages = server.wp.getPosts(blog_id, wp_user, wp_pass, {
            "post_type": "page",
            "number": 100,
            "post_status": "any",
        })
        for pg in pages:
            if pg.get("post_name") == slug:
                existing_page_id = pg["post_id"]
                link = pg.get("link", "")
                print(f"[OK] Pagina existente: ID {existing_page_id} ({link})")
                break
    except Exception as e:
        print(f"[AVISO] Nao foi possivel buscar paginas: {e}")

    if existing_page_id:
        result = server.wp.editPost(blog_id, wp_user, wp_pass,
                                     existing_page_id, {
                                         "post_title": title,
                                         "post_content": page_content,
                                         "post_status": "publish",
                                     })
        if result:
            print(f"[OK] Pagina ATUALIZADA: {wp_url.rstrip('/')}/{slug}/")
        else:
            print("[ERRO] Falha ao atualizar pagina")
            sys.exit(1)
    else:
        page_id = server.wp.newPost(blog_id, wp_user, wp_pass, {
            "post_title": title,
            "post_content": page_content,
            "post_type": "page",
            "post_status": "publish",
            "post_name": slug,
        })
        print(f"[OK] Pagina CRIADA: {wp_url.rstrip('/')}/{slug}/ (ID: {page_id})")


def main():
    parser = argparse.ArgumentParser(description="Publicar Almoxarifado no WordPress")
    parser.add_argument("--wp-url", default=WP_URL)
    parser.add_argument("--wp-user", default=WP_USER)
    parser.add_argument("--wp-pass", default=None)
    parser.add_argument("--slug", default=WP_SLUG)
    parser.add_argument("--title", default=WP_TITLE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    wp_pass = args.wp_pass or os.environ.get("WP_PASS")
    if not wp_pass and not args.dry_run:
        print("[ERRO] Informe a senha via --wp-pass ou variavel WP_PASS")
        sys.exit(1)

    print("=" * 50)
    print("  Publicar Almoxarifado no WordPress")
    print("=" * 50)
    print("\n[1/3] Extraindo dados do banco...")
    dados = extrair_dados()

    print("[2/3] Gerando HTML estatico...")
    html = generate_html(dados)
    print(f"[OK] HTML gerado: {len(html)} bytes ({len(html)/1024:.0f} KB)")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"[OK] HTML salvo em: {out_path}")

    if args.dry_run:
        print("\n[3/3] MODO DRY-RUN - Nada foi publicado")
    else:
        print("[3/3] Publicando no WordPress...")
        publicar_wordpress(html, args.wp_url, args.wp_user,
                           wp_pass, args.slug, args.title)

    print(f"\nConcluido!")
    print(f"  Pagina: {args.wp_url.rstrip('/')}/{args.slug}/")
    print(f"  Itens:  {dados['total']}")


if __name__ == "__main__":
    main()
