#!/usr/bin/env python3
"""Publish pre-generated WordPress HTML to the WordPress page."""
import xmlrpc.client, os, sys
from pathlib import Path

WP_URL = "https://fob.usp.br"
WP_USER = "brubiro"
SLUG = "estoque-almoxarifado"
TITLE = "Consulta Almoxarifado"
HTML_FILE = Path(__file__).resolve().parent.parent.parent / "almoxarifado-wordpress.html"

def main():
    wp_pass = os.environ.get("WP_PASS")
    if not wp_pass:
        print("[ERRO] Defina a variavel WP_PASS")
        print("    $env:WP_PASS = 'sua-senha'")
        sys.exit(1)

    if not HTML_FILE.exists():
        print(f"[ERRO] Arquivo nao encontrado: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(encoding="utf-8")
    print(f"[OK] HTML lido: {len(html)} bytes ({len(html)/1024:.0f} KB)")

    xmlrpc_url = WP_URL.rstrip("/") + "/xmlrpc.php"
    print(f"[..] Conectando em {xmlrpc_url} ...")
    server = xmlrpc.client.ServerProxy(xmlrpc_url)

    try:
        blogs = server.wp.getUsersBlogs(WP_USER, wp_pass)
        blog_id = blogs[0]["blogid"]
        print(f"[OK] Conectado - Blog ID: {blog_id}")
    except Exception as e:
        print(f"[ERRO] Autenticacao: {e}")
        sys.exit(1)

    # Buscar pagina existente
    existing_id = None
    try:
        pages = server.wp.getPosts(blog_id, WP_USER, wp_pass, {
            "post_type": "page", "number": 100, "post_status": "any",
        })
        for pg in pages:
            if pg.get("post_name") == SLUG:
                existing_id = pg["post_id"]
                link = pg.get("link", "")
                print(f"[OK] Pagina existente: ID {existing_id} ({link})")
                break
    except Exception as e:
        print(f"[AVISO] Nao foi possivel buscar paginas: {e}")

    if existing_id:
        result = server.wp.editPost(blog_id, WP_USER, wp_pass, existing_id, {
            "post_title": TITLE,
            "post_content": html,
            "post_status": "publish",
        })
        if result:
            print(f"[OK] Pagina ATUALIZADA: {WP_URL}/{SLUG}/")
        else:
            print("[ERRO] Falha ao atualizar pagina")
            sys.exit(1)
    else:
        page_id = server.wp.newPost(blog_id, WP_USER, wp_pass, {
            "post_title": TITLE,
            "post_content": html,
            "post_type": "page",
            "post_status": "publish",
            "post_name": SLUG,
        })
        print(f"[OK] Pagina CRIADA (ID: {page_id}): {WP_URL}/{SLUG}/")

    print("[OK] Publicacao concluida!")

if __name__ == "__main__":
    main()
