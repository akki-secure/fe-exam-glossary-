#!/usr/bin/env python3
"""fe-siken.com の用語集から、分野構成と用語名(読み・英語名)だけを取得して src/site/structure.json に保存する。
説明文は取得しない(説明文は src/data/desc/*.txt に独自に書き下ろす)。"""
import html, json, re, time, urllib.request

BASE = "https://www.fe-siken.com"
def get(path):
    for _ in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(BASE + path), timeout=30).read().decode("utf-8")
        except Exception:
            time.sleep(2)
    raise SystemExit("取得失敗: " + path)

top = get("/keyword/")
cats = []
for m in re.finditer(r'<li class="cat-card">\s*<a class="cat-card__link" href="/keyword/(\d+)/">.*?cat-card__name">([^<]+)</span>(.*?)</li>\s*(?=<li class="cat-card">|</ul>)', top, re.S):
    subs = [(a, html.unescape(b), int(c)) for a, b, c in re.findall(r'href="/keyword/\d+/([\d-]+)">([^<]+)<span class="word_count">(\d+)', m.group(3))]
    cats.append({"id": int(m.group(1)), "name": html.unescape(m.group(2)), "subs": subs})
out = []
for c in cats:
    entry = {"id": c["id"], "name": c["name"], "subs": []}
    for sid, sname, n in c["subs"]:
        page = get(f"/keyword/{c['id']}/{sid}/")
        terms = []
        for a in re.findall(r'<article class="term-article.*?</article>', page, re.S):
            t = html.unescape(re.search(r'itemprop="name">(.*?)</h3>', a, re.S).group(1).strip())
            e = re.search(r'itemprop="alternateName">(.*?)</span>', a)
            terms.append([t, html.unescape(e.group(1)) if e else ""])
        if len(terms) != n: print("語数不一致", sid, sname, n, len(terms))
        entry["subs"].append({"id": sid, "name": sname, "terms": terms})
        time.sleep(0.4)
    out.append(entry)
json.dump(out, open("src/site/structure.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sum(len(s["terms"]) for c in out for s in c["subs"]), "語")
