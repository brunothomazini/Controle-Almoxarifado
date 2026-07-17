#!/usr/bin/env python3
import xmlrpc.client, os, sys
wp_user = os.environ.get("WP_USER")
wp_pass = os.environ.get("WP_PASS")
if not wp_user or not wp_pass:
    print("[ERRO] Defina WP_USER e WP_PASS")
    sys.exit(1)
server = xmlrpc.client.ServerProxy("https://fob.usp.br/xmlrpc.php")
blogs = server.wp.getUsersBlogs(wp_user, wp_pass)
blog_id = blogs[0]["blogid"]
pages = server.wp.getPosts(blog_id, wp_user, wp_pass, {
    "post_type": "page", "number": 20, "post_status": "any",
})
print(f"{len(pages)} paginas encontradas:")
for p in pages:
    print(f'  ID {p["post_id"]}: "{p.get("post_title","?")}" -> /{p.get("post_name","?")}/ status={p.get("post_status","?")}')
