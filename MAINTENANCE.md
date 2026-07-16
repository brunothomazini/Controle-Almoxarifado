# Guia de Manutenção - Controle de Almoxarifado

Este documento detalha como atualizar os dados do sistema.

## Requisitos
- Python 3.x instalado.
- Biblioteca `requests`: `pip install requests`

## Fluxo de Atualização (Passo a Passo)

1.  **Atualizar dados (Coleta):**
    Abra o terminal na pasta raiz do projeto e execute:
    ```powershell
    python scripts/fetch.py
    ```
    *Isso baixará os dados mais recentes da FOB e salvará em `data/almox.json`.*

2.  **Gerar o Site (Build):**
    Execute o script de compilação:
    ```powershell
    python scripts/build.py
    ```
    *Isso lerá o `data/almox.json` e atualizará o arquivo `index.html`.*

3.  **Publicar:**
    Após confirmar que o `index.html` está correto, envie as alterações para o GitHub:
    ```powershell
    git add .
    git commit -m "chore: atualização de estoque"
    git push
    ```

## Resolução de Problemas
- **O script `fetch.py` falhou:** Provavelmente a estrutura da página da FOB mudou. O script precisará de um ajuste no regex (Expressão Regular).
- **Os dados não aparecem no site:** Recarregue o site com `Ctrl + F5` para limpar o cache.
