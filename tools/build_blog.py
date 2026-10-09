"""Сборка блога caloriept.ru: content/blog/<slug>.md → blog/<slug>/index.html, blog/index.html, sitemap.xml.

Запуск из корня репозитория: python tools/build_blog.py
Шапка статьи — строки «ключ: значение» до первой пустой строки: title, description, date (ГГГГ-ММ-ДД), h1, lead.
Тело: «## » и «### » заголовки, абзацы, списки «- » и «1. », таблицы «| … |», **жирный**, [текст](адрес).
Раздел «## Частые вопросы» с «### вопрос» становится ещё и разметкой FAQPage.
"""
import html
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "blog"
OUT = ROOT / "blog"
BASE = "https://caloriept.ru"
BOT = "https://t.me/Calorie_counter_rf_bot"
OG_IMAGE = "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=1200&h=630&q=80&auto=format&fit=crop"
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FAQ_TITLE = "частые вопросы"
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
          "ноября", "декабря"]
METRIKA = """<script>(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})(window,document,'script','https://mc.yandex.ru/metrika/tag.js?id=110221375','ym');ym(110221375,'init',{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true});</script>
<noscript><div><img src="https://mc.yandex.ru/watch/110221375" style="position:absolute;left:-9999px" alt=""></div></noscript>"""


@dataclass
class Article:
    slug: str
    title: str
    description: str
    date: date
    h1: str
    lead: str
    body: str
    faq: list = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"{BASE}/blog/{self.slug}/"

    @property
    def minutes(self) -> int:
        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", self.body)))
        return max(1, round(words / 180))


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)

    def link(m):
        label, url = m.group(1), m.group(2)
        if url.startswith("/"):
            return f'<a href="{html.escape(url)}">{label}</a>'
        if url.startswith("https://"):
            return f'<a href="{html.escape(url)}" rel="noopener" target="_blank">{label}</a>'
        return label
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)


def plain(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text).replace("**", "")


def _table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)]
    head, body = cells[0], cells[1:]
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
    return f'<div class="art-table"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def to_html(md: str):
    out, faq = [], []
    in_faq, question, answer = False, None, []
    lines = md.splitlines()
    i = 0

    def close_q():
        nonlocal question, answer
        if question and answer:
            faq.append((plain(question), plain(" ".join(answer))))
        question, answer = None, []

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("## "):
            close_q()
            title = line[3:].strip()
            in_faq = title.lower() == FAQ_TITLE
            out.append(f'<h2 class="rv">{inline(title)}</h2>')
            i += 1
        elif line.startswith("### "):
            close_q()
            if in_faq:
                question = line[4:].strip()
            out.append(f'<h3 class="rv">{inline(line[4:].strip())}</h3>')
            i += 1
        elif line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i]); i += 1
            out.append(_table(rows))
        elif re.match(r"\s*(-|\d+\.)\s", line):
            ordered = bool(re.match(r"\s*\d+\.", line))
            items = []
            while i < len(lines) and re.match(r"\s*(-|\d+\.)\s", lines[i]):
                items.append(re.sub(r"^\s*(-|\d+\.)\s+", "", lines[i].rstrip())); i += 1
            tag = "ol" if ordered else "ul"
            out.append(f'<{tag} class="rv">' + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            if question:
                answer.extend(items)
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(#{2,3} |\s*\||\s*(-|\d+\.)\s)", lines[i]):
                para.append(lines[i].strip()); i += 1
            text = " ".join(para)
            out.append(f'<p class="rv">{inline(text)}</p>')
            if question:
                answer.append(text)
    close_q()
    return "\n".join(out), faq


def parse(path: Path) -> Article:
    raw = path.read_text(encoding="utf-8").lstrip("﻿").replace("\r\n", "\n")
    head, _, body = raw.partition("\n\n")
    meta = {}
    for line in head.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip()
    for key in ("title", "description", "date", "h1"):
        if not meta.get(key):
            raise ValueError(f"{path.name}: нет поля «{key}» в шапке")
    body_html, faq = to_html(body)
    return Article(slug=path.stem, title=meta["title"], description=meta["description"],
                   date=date.fromisoformat(meta["date"]), h1=meta["h1"], lead=meta.get("lead", ""),
                   body=body_html, faq=faq)


def human_date(d: date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def ld_json(a: Article) -> str:
    org = {"@type": "Organization", "@id": f"{BASE}/#org", "name": "CaloriePT AI", "url": f"{BASE}/",
           "logo": f"{BASE}/icon.png"}
    graph = [
        org,
        {"@type": "Article", "headline": a.h1, "description": a.description,
         "datePublished": a.date.isoformat(), "dateModified": a.date.isoformat(), "inLanguage": "ru",
         "mainEntityOfPage": a.url, "image": OG_IMAGE,
         "author": {"@id": f"{BASE}/#org"}, "publisher": {"@id": f"{BASE}/#org"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Статьи", "item": f"{BASE}/blog/"},
            {"@type": "ListItem", "position": 3, "name": a.h1, "item": a.url}]},
    ]
    if a.faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
            for q, ans in a.faq]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


CSS = """
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0C1018;--bg2:#111620;--bg3:#161C28;--gold:#C9A96E;--gold-lt:#E2C99A;--white:#F0EDE8;--muted:#7A8399;--text:#B9C1CF;--border:rgba(201,169,110,.18)}
html{-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--white);font-family:'Inter',system-ui,sans-serif;font-weight:300;line-height:1.7;overflow-x:hidden}
a{color:var(--gold)}
.progress{position:fixed;top:0;left:0;height:2px;width:0;background:linear-gradient(90deg,var(--gold),var(--gold-lt));z-index:200}
nav{position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 60px;background:rgba(12,16,24,.85);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--border)}
.nav-logo{font-family:'Cormorant Garamond',serif;font-size:24px;font-weight:600;letter-spacing:.05em;color:var(--white);text-decoration:none}
.nav-links{display:flex;gap:32px;align-items:center}
.nav-links a{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-decoration:none;transition:color .2s}
.nav-links a:hover{color:var(--white)}
.nav-cta{font-size:11px;letter-spacing:.12em;text-transform:uppercase;padding:10px 22px;border:1px solid var(--gold);color:var(--gold)!important;text-decoration:none;transition:all .25s}
.nav-cta:hover{background:var(--gold);color:var(--bg)!important}
.wrap{max-width:760px;margin:0 auto;padding:0 24px}
.crumbs{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:48px 0 0}
.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:var(--gold)}
.art-head{padding:28px 0 40px;border-bottom:1px solid var(--border);margin-bottom:44px}
.eyebrow{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:20px}
h1{font-family:'Cormorant Garamond',serif;font-weight:300;font-size:clamp(36px,5.4vw,58px);line-height:1.08;margin-bottom:22px}
.lead{font-size:17px;color:var(--text);max-width:640px}
.meta{margin-top:22px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
article h2{font-family:'Cormorant Garamond',serif;font-weight:400;font-size:clamp(28px,3.4vw,36px);line-height:1.2;margin:56px 0 18px;color:var(--white)}
article h2::before{content:'';display:block;width:40px;height:1px;background:var(--gold);margin-bottom:18px}
article h3{font-family:'Cormorant Garamond',serif;font-weight:400;font-size:24px;margin:30px 0 10px;color:var(--gold-lt)}
article p{font-size:16px;color:var(--text);margin-bottom:16px}
article b{color:var(--white);font-weight:500}
article ul,article ol{margin:0 0 20px 0;padding-left:0;list-style:none;counter-reset:n}
article li{position:relative;padding-left:30px;margin-bottom:10px;color:var(--text);font-size:16px}
article ul li::before{content:'→';position:absolute;left:0;color:var(--gold)}
article ol li{counter-increment:n}
article ol li::before{content:counter(n,decimal-leading-zero);position:absolute;left:0;font-family:'Cormorant Garamond',serif;color:var(--gold);font-size:18px;line-height:1.5}
article a{color:var(--gold);text-decoration:none;border-bottom:1px solid rgba(201,169,110,.35);transition:border-color .2s}
article a:hover{border-color:var(--gold)}
.art-table{overflow-x:auto;margin:8px 0 26px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{background:var(--bg3);color:var(--gold);font-weight:500;text-align:left;padding:12px 16px;font-size:11px;letter-spacing:.1em;text-transform:uppercase}
td{padding:12px 16px;border-top:1px solid var(--border);color:var(--text);vertical-align:top}
.cta-box{position:relative;margin:64px 0 40px;padding:48px 40px;text-align:center;background:var(--bg2);border:1px solid var(--border);overflow:hidden}
.cta-box::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse 60% 60% at 50% 0%,rgba(201,169,110,.12),transparent 70%);pointer-events:none}
.cta-box h2{margin:0 0 12px!important}.cta-box h2::before{display:none}
.cta-box p{margin-bottom:28px}
.btn{display:inline-block;padding:16px 40px;background:var(--gold);color:var(--bg)!important;font-size:11px;letter-spacing:.15em;text-transform:uppercase;text-decoration:none;font-weight:500;border:0!important;transition:background .25s,transform .25s;position:relative}
.btn:hover{background:var(--gold-lt);transform:translateY(-1px)}
.note{font-size:13px!important;color:var(--muted)!important;border-left:1px solid var(--gold);padding-left:16px;margin-top:32px}
.more{border-top:1px solid var(--border);margin-top:56px;padding-top:40px}
.more-title{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1px;background:var(--border);border:1px solid var(--border)}
.card{display:block;background:var(--bg2);padding:32px 28px;text-decoration:none;position:relative;overflow:hidden;transition:background .3s}
.card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);transform:scaleX(0);transform-origin:left;transition:transform .45s ease}
.card:hover{background:var(--bg3)}.card:hover::after{transform:scaleX(1)}
.card-date{font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
.card-title{font-family:'Cormorant Garamond',serif;font-size:24px;line-height:1.2;color:var(--white);margin-bottom:10px}
.card-text{font-size:13px;color:var(--muted);line-height:1.7}
footer{border-top:1px solid var(--border);margin-top:80px;padding:40px 60px;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;background:var(--bg2);font-size:11px;color:var(--muted);letter-spacing:.08em}
footer a{color:var(--muted);text-decoration:none;text-transform:uppercase}footer a:hover{color:var(--gold)}
.rv{opacity:1}
html.anim .rv{opacity:0;transform:translateY(18px);transition:opacity .7s ease,transform .7s ease}
html.anim .rv.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){html.anim .rv{opacity:1;transform:none;transition:none}}
@media (max-width:760px){th,td{padding:10px 8px;font-size:13px}th{font-size:10px;letter-spacing:.06em}nav{padding:14px 16px}.nav-links a:not(.nav-cta){display:none}.wrap{padding:0 16px}.cta-box{padding:36px 20px}footer{padding:32px 16px;flex-direction:column}}
"""

SCRIPT = """<script>
(function(){var d=document.documentElement;if(!('IntersectionObserver' in window))return;d.classList.add('anim');
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}})},{rootMargin:'0px 0px -8% 0px'});
document.querySelectorAll('.rv').forEach(function(el){io.observe(el)});
var bar=document.querySelector('.progress');if(bar){addEventListener('scroll',function(){var h=d.scrollHeight-innerHeight;bar.style.width=(h>0?scrollY/h*100:0)+'%'},{passive:true});}
})();
</script>"""


def page(title, description, canonical, body, ld="", og_type="website"):
    t, desc = html.escape(title), html.escape(description)
    ld_tag = f'<script type="application/ld+json">{ld}</script>' if ld else ""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="CaloriePT AI">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0C1018">
<link rel="icon" href="/icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
{ld_tag}
{METRIKA}
</head>
<body>
<div class="progress"></div>
<nav>
  <a class="nav-logo" href="/">CaloriePT AI 2.0</a>
  <div class="nav-links">
    <a href="/#features">Возможности</a>
    <a href="/blog/">Статьи</a>
    <a class="nav-cta" href="{BOT}" target="_blank" rel="noopener">Попробовать</a>
  </div>
</nav>
{body}
<footer>
  <span>© 2026 CaloriePT AI · Студия DimkoFF</span>
  <span><a href="/">Главная</a> &nbsp;·&nbsp; <a href="/blog/">Статьи</a> &nbsp;·&nbsp; <a href="{BOT}" target="_blank" rel="noopener">Telegram-бот</a></span>
</footer>
{SCRIPT}
</body>
</html>
"""


def card(a: Article) -> str:
    return (f'<a class="card rv" href="/blog/{a.slug}/"><div class="card-date">{human_date(a.date)} · {a.minutes} мин</div>'
            f'<div class="card-title">{html.escape(a.h1)}</div><div class="card-text">{html.escape(a.description)}</div></a>')


def render_article(a: Article, others) -> str:
    more = ""
    if others:
        more = ('<div class="more"><div class="more-title">Читайте также</div><div class="cards">'
                + "".join(card(o) for o in others[:3]) + "</div></div>")
    body = f"""<main class="wrap">
  <div class="crumbs"><a href="/">Главная</a> / <a href="/blog/">Статьи</a></div>
  <header class="art-head">
    <p class="eyebrow">CaloriePT · Питание</p>
    <h1>{html.escape(a.h1)}</h1>
    <p class="lead">{inline(a.lead)}</p>
    <div class="meta">{human_date(a.date)} · {a.minutes} мин чтения</div>
  </header>
  <article>
{a.body}
  <p class="note">Материал носит справочный характер и не заменяет консультацию врача или диетолога. При заболеваниях, беременности и в подростковом возрасте нормы питания подбирает специалист.</p>
  </article>
  <section class="cta-box rv">
    <h2>Считайте калории по фото в Telegram</h2>
    <p>CaloriePT AI рассчитает вашу норму, распознает блюдо по фото и сам заполнит дневник питания.</p>
    <a class="btn" href="{BOT}" target="_blank" rel="noopener">Открыть бота</a>
  </section>
  {more}
</main>"""
    return page(a.title, a.description, a.url, body, ld_json(a), og_type="article")


def render_index(arts) -> str:
    ld = json.dumps({"@context": "https://schema.org", "@type": "Blog", "name": "Статьи CaloriePT AI",
                     "url": f"{BASE}/blog/", "inLanguage": "ru",
                     "blogPost": [{"@type": "BlogPosting", "headline": a.h1, "url": a.url,
                                   "datePublished": a.date.isoformat()} for a in arts]}, ensure_ascii=False)
    body = f"""<main class="wrap" style="max-width:1100px">
  <div class="crumbs"><a href="/">Главная</a> / Статьи</div>
  <header class="art-head">
    <p class="eyebrow">Статьи</p>
    <h1>Питание, калории и КБЖУ — <em style="color:var(--gold)">простым языком</em></h1>
    <p class="lead">Как считать калории, рассчитать свою норму и вести дневник питания без лишних приложений.</p>
  </header>
  <div class="cards">{"".join(card(a) for a in arts)}</div>
</main>"""
    return page("Статьи о питании и подсчёте калорий — CaloriePT AI",
                "Как считать калории и КБЖУ, рассчитать норму калорий и вести дневник питания. Статьи CaloriePT AI.",
                f"{BASE}/blog/", body, ld)


def sitemap(arts) -> str:
    today = date.today().isoformat()
    urls = [(f"{BASE}/", today), (f"{BASE}/blog/", arts[0].date.isoformat() if arts else today)]
    urls += [(a.url, a.date.isoformat()) for a in arts]
    items = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>\n'


def main():
    arts = sorted((parse(p) for p in SRC.glob("*.md") if SLUG_RE.fullmatch(p.stem)),
                  key=lambda a: (a.date, a.slug), reverse=True)
    for a in arts:
        target = OUT / a.slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        others = [o for o in arts if o.slug != a.slug]
        target.write_text(render_article(a, others), encoding="utf-8", newline="\n")
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render_index(arts), encoding="utf-8", newline="\n")
    (ROOT / "sitemap.xml").write_text(sitemap(arts), encoding="utf-8", newline="\n")
    print(f"Собрано статей: {len(arts)}")


if __name__ == "__main__":
    main()
