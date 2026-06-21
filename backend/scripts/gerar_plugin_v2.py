#!/usr/bin/env python3
import base64, json, sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent
DB = BASE / "backend" / "data" / "almoxarifado.db"
OUT = BASE / "plugins" / "almoxarifado-plugin" / "almoxarifado-consulta.php"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
categorias = [r["nome"] for r in cur.fetchall()]

cur.execute("SELECT id, nome FROM categorias")
cat_map = {r["id"]: r["nome"] for r in cur.fetchall()}

cur.execute(
    "SELECT i.codigo,i.nome,i.nome_comercial,i.fabricante,i.categoria_id,"
    "i.quantidade_atual,i.unidade_medida,i.solicitar_por_email,i.tipo_controle,i.status "
    "FROM itens i ORDER BY i.nome"
)
itens = []
for r in cur.fetchall():
    row = dict(r)
    cn = cat_map.get(row["categoria_id"], "N/A")
    tc = (row["tipo_controle"] or "").lower()
    if cn == "Informatica":
        ped = "solicitar para o setor de Informatica"
    elif tc == "almoxarifado":
        ped = "Almox"
    elif row["solicitar_por_email"]:
        ped = "e-mail padronizados@fob.usp.br"
    else:
        ped = "Almox"
    itens.append({
        "c": row["codigo"], "n": row["nome"],
        "nc": row["nome_comercial"] or "-",
        "f": row["fabricante"] or "-",
        "cat": cn,
        "s": str.lower(row["status"] or "DISPONIVEL"),
        "p": ped,
    })
conn.close()

total = len(itens)
disp = sum(1 for i in itens if i["s"] == "disponivel")
data_json = json.dumps({"itens": itens, "cats": categorias}, ensure_ascii=False)
cat_opts = "\n".join(f"<option value=\"{c}\">{c}</option>" for c in categorias)
hoje = datetime.now().strftime("%d/%m/%Y")

# Gerar HTML limpo (sem html/head/body)
html = f"""<style>
#az h2{{margin-top:0;font-size:1.15rem;color:#1094ab;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #e9e9e9}}
#az .hdr{{background:linear-gradient(135deg,#055e6f,#1094ab);color:#fff;padding:20px 0;box-shadow:0 2px 8px rgba(0,0,0,.15)}}
#az .hdr-in{{max-width:100%;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between}}
#az .hdr h1{{font-size:1.5rem;font-weight:600;margin:0}}
#az .hdr .sub{{font-size:.85rem;opacity:.85;margin-top:2px}}
#az .ct{{max-width:100%;margin:0 auto;padding:20px}}
#az .cd{{background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:24px;margin-bottom:20px}}
#az .sb{{display:flex;gap:12px;flex-wrap:wrap}}
#az .sb input,#az .sb select{{padding:10px 14px;border:1px solid #ddd;border-radius:6px;font-size:.95rem;flex:1;min-width:180px;outline:none}}
#az .sb input:focus,#az .sb select:focus{{border-color:#1094ab;box-shadow:0 0 0 3px rgba(16,148,171,.1)}}
#az .bt{{display:inline-block;padding:10px 24px;background:#1094ab;color:#fff;border:none;border-radius:6px;font-size:.95rem;cursor:pointer;white-space:nowrap;text-decoration:none}}
#az .bt:hover{{background:#055e6f}}
#az .bt-o{{background:transparent;color:#1094ab;border:1px solid #1094ab}}
#az .bt-o:hover{{background:#f5f5f5}}
#az .st{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px}}
#az .sc{{background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:18px;text-align:center}}
#az .sc .n{{font-size:2rem;font-weight:700;color:#1094ab}}
#az .sc .l{{font-size:.85rem;color:#666}}
#az .sc.g .n{{color:#4caf50}}
#az .sc.r .n{{color:#f44336}}
#az .ft{{text-align:center;padding:20px;color:#999;font-size:.85rem}}
#az .upd{{font-size:.82rem;color:#999;text-align:center;margin-bottom:16px}}
#az table{{width:100%;border-collapse:collapse;font-size:.9rem}}
#az th{{background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#055e6f;border-bottom:2px solid #ddd}}
#az td{{padding:10px 12px;border-bottom:1px solid #f5f5f5}}
#az .inf{{margin-bottom:12px;color:#666;font-size:.85rem}}
#az .pag{{margin-top:12px;text-align:center;display:flex;justify-content:center;align-items:center;gap:8px}}
#az .pag .bt{{padding:6px 14px;font-size:.88rem}}
#az .pag span{{font-size:.9rem;color:#555}}
#az .tag{{display:inline-block;background:#f5f5f5;padding:2px 8px;border-radius:4px;font-size:.8rem;color:#666}}
#az .wr{{overflow-x:auto;max-width:100%}}
#az td{{word-break:break-word}}
#az .emp{{text-align:center;padding:40px;color:#999}}
@media(max-width:768px){{#az .hdr-in{{flex-direction:column;text-align:center;gap:8px}}#az .sb{{flex-direction:column}}#az .sb input{{min-width:auto}}#az .st{{grid-template-columns:1fr 1fr}}#az th,#az td{{padding:6px 8px;font-size:.8rem}}}}
</style>
<div id="az" style="font-family:Roboto,'Segoe UI',Arial,sans-serif;background:transparent;color:#444;line-height:1.6">
<div class="hdr"><div class="hdr-in"><div><h1>Sistema de Controle de Almoxarifado</h1><div class="sub">Universidade de Sao Paulo &mdash; Consulta Publica</div></div></div></div>
<div class="ct">
<div class="upd">Ultima atualizacao: {hoje}</div>
<div class="st">
<div class="sc"><div class="n">{total}</div><div class="l">Itens no Estoque</div></div>
<div class="sc"><div class="n">{len(categorias)}</div><div class="l">Categorias</div></div>
<div class="sc g"><div class="n">{disp}</div><div class="l">Disponiveis</div></div>
<div class="sc r"><div class="n">{total - disp}</div><div class="l">Indisponiveis / Baixados</div></div>
</div>
<div class="cd">
<h2>Consultar Itens</h2>
<div class="sb">
<input type="text" id="z_c" placeholder="Codigo..." oninput="z_f()">
<input type="text" id="z_n" placeholder="Nome do item..." oninput="z_f()">
<select id="z_t" onchange="z_f()"><option value="">Todas as categorias</option>{cat_opts}</select>
<a class="bt" href="javascript:z_f()">Buscar</a>
<a class="bt bt-o" href="javascript:z_l()">Limpar</a>
</div>
</div>
<div class="cd"><h2>Resultados</h2><div class="wr"><div id="z_r"><div class="emp">Carregando dados...</div></div></div></div>
</div>
<div class="ft">Sistema de Controle de Almoxarifado &mdash; USP</div>
</div>
<script>
var zD={data_json};
var zI=zD.itens,zC=zD.cats,zP=50,zp=1,zF=[];
var zS=document.getElementById("z_t");
zS.innerHTML="<option value=\"\">Todas as categorias</option>";
for(var i=0;i<zC.length;i++){{var o=document.createElement("option");o.value=zC[i];o.textContent=zC[i];zS.appendChild(o);}}
function z_b(s){{var m={{disponivel:["Disponivel","#e8f5e9","#2e7d32","#4caf50"],emprestado:["Emprestado","#fff3e0","#e65100","#ff9800"],manutencao:["Manutencao","#fff3e0","#e65100","#ff9800"],baixado:["Baixado","#ffebee","#c62828","#f44336"],reservado:["Reservado","#fff3e0","#e65100","#ff9800"]}};var a=m[s]||["Desconhecido","#fff3e0","#e65100","#ff9800"];return "<span style=\"display:inline-flex;align-items:center;gap:6px\"><span style=\"width:8px;height:8px;border-radius:50%;display:inline-block;background:"+a[3]+"\"></span><span style=\"display:inline-block;padding:3px 10px;border-radius:20px;font-size:.8rem;font-weight:500;background:"+a[1]+";color:"+a[2]+"\">"+a[0]+"</span></span>";}}
function z_f(){{var a=document.getElementById("z_c").value.trim().toLowerCase();var b=document.getElementById("z_n").value.trim().toLowerCase();var c=document.getElementById("z_t").value;zF=zI.filter(function(i){{if(a&&i.c.toLowerCase().indexOf(a)===-1)return false;if(b&&i.n.toLowerCase().indexOf(b)===-1)return false;if(c&&i.cat!==c)return false;return true;}});zp=1;z_r();}}
function z_l(){{document.getElementById("z_c").value="";document.getElementById("z_n").value="";document.getElementById("z_t").value="";zF=zI.slice();zp=1;z_r();}}
function z_r(){{var e=document.getElementById("z_r"),t=zF.length,tp=Math.max(1,Math.ceil(t/zP));if(zp>tp)zp=tp;if(zp<1)zp=1;var s=(zp-1)*zP,o=Math.min(s+zP,t),pg=zF.slice(s,o);if(t===0){{e.innerHTML="<div class=\"emp\">Nenhum item encontrado</div>";return;}}var h="<div class=\"inf\">Mostrando "+(s+1)+"-"+o+" de "+t+" item(ns)</div><table><thead><tr><th>Codigo</th><th>Nome</th><th>Nome Comercial</th><th>Marca</th><th>Categoria</th><th>Pedidos por:</th><th>Status</th></tr></thead><tbody>";for(var i=0;i<pg.length;i++){{var x=pg[i];h+="<tr><td><strong>"+(x.c||"-")+"</strong></td><td>"+(x.n||"-")+"</td><td>"+(x.nc||"-")+"</td><td>"+(x.f||"-")+"</td><td><span class=\"tag\">"+(x.cat||"N/A")+"</span></td><td>"+(x.p||"Almox")+"</td><td>"+z_b(x.s)+"</td></tr>";}}h+="</tbody></table>";if(tp>1){{h+="<div class=\"pag\">";if(zp>1)h+="<a class=\"bt bt-o\" href=\"javascript:z_g("+(zp-1)+')\">&laquo; Anterior</a>";h+="<span>Pagina "+zp+" de "+tp+"</span>";if(zp<tp)h+="<a class=\"bt bt-o\" href=\"javascript:z_g("+(zp+1)+')\">Proxima &raquo;</a>";h+="</div>";}}e.innerHTML=h;}}
function z_g(x){{if(x<1)return;zp=x;z_r();}}
zF=zI.slice();z_r();
</script>"""

b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
print(f"HTML limpo: {len(html)} bytes, Base64: {len(b64)} chars")

php = f"""<?php
/**
 * Plugin Name: Almoxarifado - Consulta Pública
 * Description: Sistema de consulta de estoque do almoxarifado FOB/USP
 * Version: 1.0
 */

function almoxarifado_plugin_output() {{
    return base64_decode("{b64}");
}}
add_shortcode('almoxarifado', 'almoxarifado_plugin_output');
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(php, encoding="utf-8")
print(f"[OK] Plugin: {OUT} ({len(php)} bytes)")
