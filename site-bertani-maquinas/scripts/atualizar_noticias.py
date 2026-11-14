"""Busca manchetes recentes sobre costura e confecção (Botucatu, região e setor)
no Google Notícias e grava noticias.json para o site.
Roda sozinho uma vez por dia (ver .github/workflows/noticias.yml).
Só guarda título, fonte, data e link: o leitor abre a matéria no site original."""
import json, datetime, email.utils, urllib.parse, urllib.request, xml.etree.ElementTree as ET

BUSCAS = [
    '"Botucatu" costura OR confecção OR têxtil',
    'confecção interior de São Paulo',
    '"máquina de costura" OR "máquinas de costura"',
    'Abit indústria têxtil confecção',
]
MAX_DIAS = 45
MAX_ITENS = 6
BLOQUEAR = ["acidente", "morte", "polícia", "preso", "crime"]  # mantém o tom da loja

def buscar(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + f" when:{MAX_DIAS}d", "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (site Bertani Maquinas)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    for it in root.iter("item"):
        titulo = it.findtext("title", "")
        fonte = it.findtext("source", "") or ""
        if fonte and titulo.endswith(" - " + fonte):
            titulo = titulo[: -len(fonte) - 3]
        quando = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        yield {"titulo": titulo.strip(), "fonte": fonte, "link": it.findtext("link"), "quando": quando}

def main():
    vistos, itens = set(), []
    for q in BUSCAS:
        try:
            for n in buscar(q):
                chave = n["titulo"].lower()[:60]
                if chave in vistos or any(b in chave for b in BLOQUEAR):
                    continue
                vistos.add(chave); itens.append(n)
        except Exception as e:
            print("falhou:", q, e)
    if not itens:
        print("Nenhuma notícia nova; mantendo o arquivo anterior."); return
    itens.sort(key=lambda n: n["quando"], reverse=True)
    saida = {
        "atualizado_em": datetime.date.today().strftime("%d/%m/%Y"),
        "itens": [{"titulo": n["titulo"], "fonte": n["fonte"], "link": n["link"],
                   "data": n["quando"].strftime("%d/%m/%Y")} for n in itens[:MAX_ITENS]],
    }
    with open("noticias.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"{len(saida['itens'])} notícias gravadas.")

if __name__ == "__main__":
    main()
