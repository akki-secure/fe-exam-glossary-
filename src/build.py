#!/usr/bin/env python3
"""src/data/*.txt から カード形式・穴埋め形式のHTMLと index.html を生成する。

データ形式:
  @meta タイトル|パンくず|導入文
  @group グループ名|グループ説明
  用語|説明|例(省略可)
"""
import glob, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "src", "data")

# (大分類, [(slug, 表示名)])  ※既存4ページは手書きHTMLのため index にのみ載せる
CATEGORIES = [
    ("基礎理論", [("discrete-math", "離散数学編"), ("applied-math", "応用数学編"),
                 ("info-theory", "情報理論編"), ("comm-theory", "通信理論編"),
                 ("algo", "アルゴリズムとプログラミング編")]),
    ("コンピュータシステム", [("processor", "コンピュータ構成要素編"), ("sysconf", "システム構成要素編"),
                     ("software", "ソフトウェア編"), ("hardware", "ハードウェア編")]),
    ("技術要素", [("ui-media", "ユーザーインタフェース・情報メディア編"), ("database", "データベース編"),
               ("network", "ネットワーク編"), ("security", "セキュリティ編")]),
    ("開発技術", [("sysdev", "システム開発技術編"), ("swmgmt", "ソフトウェア開発管理技術編")]),
    ("マネジメント", [("project", "プロジェクトマネジメント編"), ("service", "サービスマネジメント編"),
                 ("audit", "システム監査編")]),
    ("ストラテジ", [("sys-strategy", "システム戦略編"), ("biz-strategy", "経営戦略編"),
                ("corp-legal", "企業活動と法務編")]),
]
HAND_MADE = {"discrete-math", "applied-math", "info-theory", "comm-theory"}
ALL = [s for _, items in CATEGORIES for s in items]

def esc(s): return html.escape(s, quote=False)

def css(kind):
    src = open(os.path.join(ROOT, f"comm-theory-{kind}.html"), encoding="utf-8").read()
    return re.search(r"<style>.*?</style>", src, re.S).group(0)

def parse(path):
    meta, groups = None, []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"): continue
        if line.startswith("@meta "):
            meta = line[6:].split("|")
        elif line.startswith("@group "):
            n, d = (line[7:].split("|") + [""])[:2]
            groups.append((n, d, []))
        else:
            p = line.split("|")
            if len(p) < 2: sys.exit(f"形式エラー {path}: {line}")
            groups[-1][2].append((p[0], p[1], p[2] if len(p) > 2 and p[2] else None))
    return meta, groups

def nav(slug, kind):
    i = [s for s, _ in ALL].index(slug)
    prev = ALL[i - 1] if i > 0 else None
    nxt = ALL[i + 1] if i + 1 < len(ALL) else None
    def cur(k): return ' aria-current="page"' if k == kind else ""
    out = ['    <nav class="page-nav" aria-label="ページ切り替え">',
           '      <div class="nav-group"><a href="index.html">目次</a></div>',
           '      <span class="nav-sep">|</span>',
           '      <div class="nav-group">',
           f'        <span class="nav-label">{esc(dict(ALL)[slug])}</span>',
           f'        <a href="{slug}-cards.html"{cur("cards")}>カード</a>',
           '        <span class="nav-sep">/</span>',
           f'        <a href="{slug}-quiz.html"{cur("quiz")}>穴埋め</a>', '      </div>']
    for lab, t in (("← 前", prev), ("次 →", nxt)):
        if t:
            out += ['      <span class="nav-sep">|</span>',
                    f'      <div class="nav-group"><a href="{t[0]}-{"cards" if kind=="cards" else "quiz"}.html">{lab}: {esc(t[1])}</a></div>']
    out.append('    </nav>')
    return "\n".join(out)

FOOT = '  <footer class="page-footer">出典: fe-siken.com「基本情報技術者試験ドットコム」の用語集構成(シラバスVer9.2)を参考に、説明文を平易な表現で独自に書き下ろして作成。</footer>'

def page(slug, kind, meta, groups):
    title, crumb, intro = meta
    n = sum(len(g[2]) for g in groups)
    q = kind == "quiz"
    h = [f'<title>{esc(title)}{"(穴埋め)" if q else ""} — 基本情報技術者試験 用語集</title>', css(kind), '<div class="page">',
         nav(slug, kind), '  <header class="masthead">',
         f'    <p class="breadcrumb">{esc(crumb)}{" &gt; 穴埋め問題" if q else ""}</p>',
         f'    <h1>{esc(title)}{"(穴埋め)" if q else ""}</h1>', '    <div class="meta-row">',
         f'      <span class="count-badge">{n} 語</span>',
         '      <span class="source-note">fe-siken.com 用語集(シラバスVer9.2)をもとに作成</span>', '    </div>']
    if not q: h.append(f'    <p class="intro">{esc(intro)}</p>')
    h.append('  </header>')
    for gn, gd, terms in groups:
        h += ['  <section class="group">', f'    <p class="group-label">{esc(gn)}</p>']
        if not q: h.append(f'    <p class="group-desc">{esc(gd)}</p>')
        h.append('    <hr class="group-divider" />')
        h.append('    <div class="term-list">' if q else '    <dl class="term-list">')
        for t, d, e in terms:
            if q:
                h.append(f'      <p class="term-line"><span class="bullet">・</span>(　　　　　　　　) <span class="arrow">→</span>{esc(d)}{esc(e) if e else ""}</p>')
            else:
                h += ['      <div class="term-entry">',
                      f'        <dt class="term"><span class="arrow">・</span>{esc(t)}</dt>',
                      f'        <dd class="desc">{esc(d)}</dd>']
                if e: h.append(f'        <p class="example"><span class="ex-label">例</span>{esc(e)}</p>')
                h.append('      </div>')
        h += ['    </div>' if q else '    </dl>', '  </section>']
    h += [FOOT, '</div>']
    return "\n".join(h) + "\n"

def index(counts):
    total = sum(counts.values())
    rows = []
    for cat, items in CATEGORIES:
        rows.append(f'  <section class="group"><p class="group-label">{esc(cat)}</p><hr class="group-divider" /><div class="term-list">')
        for s, name in items:
            rows.append(f'    <p class="term-line"><span class="bullet">・</span><strong>{esc(name)}</strong>({counts[s]}語) <span class="arrow">→</span>'
                        f'<a href="{s}-cards.html">カード</a> / <a href="{s}-quiz.html">穴埋め</a></p>')
        rows.append('  </div></section>')
    style = css("quiz").replace("</style>", "  a { color: var(--accent); }\n</style>")
    return (f'<title>目次 — 基本情報技術者試験 用語集</title>\n{style}\n<div class="page">\n  <header class="masthead">\n'
            f'    <p class="breadcrumb">fe-exam-glossary</p>\n    <h1>基本情報技術者試験 用語集</h1>\n    <div class="meta-row">'
            f'<span class="count-badge">{total} 語</span><span class="source-note">カード形式・穴埋め形式の2種類</span></div>\n  </header>\n'
            + "\n".join(rows) + f'\n{FOOT}\n</div>\n')

def main():
    counts = {}
    have = lambda s: s in HAND_MADE or os.path.exists(os.path.join(DATA, f"{s}.txt"))
    ALL[:] = [x for x in ALL if have(x[0])]
    for s, _ in ALL:
        if s in HAND_MADE:
            _, g = None, None
            src = open(os.path.join(ROOT, f"{s}-cards.html"), encoding="utf-8").read()
            counts[s] = int(re.search(r'count-badge">(\d+)', src).group(1))
            continue
        p = os.path.join(DATA, f"{s}.txt")
        meta, groups = parse(p)
        counts[s] = sum(len(g[2]) for g in groups)
        for kind in ("cards", "quiz"):
            open(os.path.join(ROOT, f"{s}-{kind}.html"), "w", encoding="utf-8").write(page(s, kind, meta, groups))
    for cat in range(len(CATEGORIES)):
        CATEGORIES[cat] = (CATEGORIES[cat][0], [x for x in CATEGORIES[cat][1] if x[0] in counts])
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index(counts))
    print(counts, sum(counts.values()))

main()
