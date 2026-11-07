# -*- coding: utf-8 -*-
"""
J16 HKBReader - build news-cache.json from the News Feed List (HIS Tools Base)
------------------------------------------------------------------------------
來源清單不再寫死：讀同目錄的 news-sources.json（由 sync_news_sources.py 從
飛書「News Feed List」(tblHXtZC4Dc0RpEQ, view vewFb7ZCho) 抽出 Job ID → J16 的所有來源）。

  news-sources.json  [{"name":"政府新聞","type":"RSS","url":"https://…"},
                      {"name":"博客","type":"Webpage","url":"https://…"}]

支援 Source Type：
  RSS / Atom  → 解析 feed（title / link / pubDate / description / 圖）
  Webpage     → 抓該頁，抽同網域的近期文章連結（無日期則排在後面）
  Youtube 等  → 跳過（不是文章列表，前端另有用途）

若 news-sources.json 不存在，回退到單一政府新聞網 RSS。

輸出：news-cache.json（前端 Tab4 用）+ news-img/*.jpg（本地縮圖）
"""
import json, os, re, html, hashlib, datetime, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "news-cache.json")
SRC_FILE = os.path.join(BASE_DIR, "news-sources.json")
LIMIT = 80
PER_WEB = 15
IMGDIR = os.path.join(BASE_DIR, "news-img")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HKBReader/1.0"
DEFAULT_SRC = [{"name": "政府新聞", "type": "RSS",
                "url": "https://www.news.gov.hk/tc/common/html/ticker.rss.xml"}]

TAG_RE = re.compile(r"<[^>]+>")
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
WS_RE = re.compile(r"[ \t\u00a0]+")
A_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
SKIP_WORDS = ("首頁", "主頁", "關於", "聯絡", "聯繫", "標籤", "分類", "更多", "上一頁",
              "下一頁", "登入", "登錄", "搜尋", "搜索", "訂閱", "RSS", "Facebook",
              "Twitter", "Instagram", "YouTube", "私隱", "條款", "廣告", "簡介", "作者簡介")


def get_bytes(url, referer=None, timeout=30):
    hdr = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        hdr["Referer"] = referer
    req = urllib.request.Request(url, headers=hdr)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get_content_charset()


def decode(data, charset=None):
    for enc in ([charset] if charset else []) + ["utf-8", "gb18030", "big5"]:
        if not enc:
            continue
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", "ignore")


def cache_image(url, referer=None):
    """遠端圖有防外連，改為下載本地副本；回傳（相對路徑, 原始網址）。"""
    if not url:
        return "", ""
    name = hashlib.md5(url.encode("utf-8")).hexdigest()[:16] + ".jpg"
    path = os.path.join(IMGDIR, name)
    rel = "news-img/" + name
    if os.path.exists(path) and os.path.getsize(path) > 512:
        return rel, url
    try:
        data, _ = get_bytes(url, referer=referer, timeout=25)
        if len(data) < 512:
            return "", url
        try:
            from PIL import Image
            import io
            im = Image.open(io.BytesIO(data)).convert("RGB")
            w, h = im.size
            if max(w, h) > 480:
                r = 480 / max(w, h)
                im = im.resize((int(w * r), int(h * r)), Image.LANCZOS)
            im.save(path, "JPEG", quality=78, optimize=True)
        except Exception:
            with open(path, "wb") as f:
                f.write(data)
        return rel, url
    except Exception as e:
        print("  img fail:", str(e)[:80])
        return "", url


def clean_text(raw):
    if not raw:
        return ""
    t = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    t = re.sub(r"</p>", "\n", t, flags=re.I)
    t = TAG_RE.sub("", t)
    t = html.unescape(t)
    t = "\n".join(WS_RE.sub(" ", ln).strip() for ln in t.split("\n"))
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def parse_date(raw):
    """'Fri, 06 Nov 2026 00:00:00 +0800' -> ('2026-11-06','00:00')"""
    if not raw:
        return "", ""
    s = raw.strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(s[:len(datetime.datetime.now().strftime(fmt)) + 8], fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0), ""
    return s[:10], ""


def rss_items(src):
    data, charset = get_bytes(src["url"])
    url = src["url"]
    root = ET.fromstring(data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    channel = root.find("channel")
    is_atom = channel is None and root.tag.endswith("feed")
    entries = []
    if is_atom:
        for e in root.findall("atom:entry", ns):
            entries.append({
                "title": e.findtext("atom:title", default="", namespaces=ns),
                "link": (e.findtext("atom:link", default="", namespaces=ns) or
                         (e.find("atom:link", ns).get("href") if e.find("atom:link", ns) is not None else "")),
                "desc": (e.findtext("atom:summary", default="", namespaces=ns) or
                         e.findtext("atom:content", default="", namespaces=ns)),
                "pub": (e.findtext("atom:updated", default="", namespaces=ns) or
                        e.findtext("atom:published", default="", namespaces=ns)),
                "cat": "",
            })
        feed_title = root.findtext("atom:title", default="", namespaces=ns)
        feed_date = root.findtext("atom:updated", default="", namespaces=ns)
    else:
        if channel is None:
            channel = root
        for it in channel.findall("item"):
            entries.append({
                "title": it.findtext("title") or "",
                "link": (it.findtext("link") or it.findtext("guid") or "").strip(),
                "desc": it.findtext("description") or "",
                "pub": it.findtext("pubDate") or "",
                "cat": clean_text(it.findtext("category")),
            })
        feed_title = clean_text(channel.findtext("title")) or src["name"]
        feed_date = channel.findtext("lastBuildDate") or ""

    items = []
    for e in entries:
        link = e["link"].strip()
        if not link:
            continue
        raw_desc = e["desc"] or ""
        m = IMG_RE.search(raw_desc)
        raw_img = m.group(1) if m else ""
        if raw_img.startswith("/"):
            raw_img = urllib.parse.urljoin(url, raw_img)
        if raw_img and not raw_img.startswith("http"):
            raw_img = ""
        img, img_src = cache_image(raw_img, referer=url)
        d, t = parse_date(e["pub"])
        items.append({
            "title": clean_text(e["title"]),
            "link": link,
            "date": d,
            "time": t,
            "summary": clean_text(raw_desc)[:260],
            "img": img,
            "imgSrc": img_src,
            "cat": e["cat"],
            "src": src["name"],
        })
    return items, feed_title, feed_date


def page_items(src):
    """Webpage 來源：抽同網域的文章連結（標題／日期／摘要／縮圖）。
    優先用「卡片區塊」解析（master-insight 的 row r2-box：圖＋<h3>標題＋作者+日期＋摘要），
    區塊解析失敗才回退到純連結掃描（此時沒有日期）。"""
    page_url = src["url"]
    host = urllib.parse.urlparse(page_url).netloc
    data, charset = get_bytes(page_url)
    text = decode(data, charset)

    CARD_RE = re.compile(r'<div class="row r2-box[^"]*"', re.I)
    DATE_IN_AUTHOR = re.compile(r"fa-clock[^>]*>\s*</i>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
    DATE_ANY = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2})")

    chunks = CARD_RE.split(text)
    out, seen = [], set()
    if len(chunks) > 1:
        for blk in chunks[1:]:
            m_url = re.search(r'href="([^"]+)"', blk)
            m_h3 = re.search(r"<h3[^>]*>(.*?)</h3>", blk, re.S)
            if not (m_url and m_h3):
                continue
            href = urllib.parse.urljoin(page_url, m_url.group(1))
            if urllib.parse.urlparse(href).netloc != host:
                continue
            title = WS_RE.sub(" ", clean_text(m_h3.group(1))).strip()
            if len(title) < 6:
                continue
            if any(w in title for w in SKIP_WORDS):
                continue
            if href in seen or href.rstrip("/") == page_url.rstrip("/"):
                continue
            seen.add(href)
            m_d = DATE_IN_AUTHOR.search(blk) or DATE_ANY.search(blk)
            d = m_d.group(1) if m_d else ""
            m_des = re.search(r'<div class="des">(.*?)</div>', blk, re.S)
            summary = clean_text(m_des.group(1))[:260] if m_des else ""
            m_img = re.search(r'<img[^>]+src="([^"]+)"', blk, re.I)
            raw_img = m_img.group(1) if m_img else ""
            if raw_img.startswith("/"):
                raw_img = urllib.parse.urljoin(page_url, raw_img)
            if raw_img and not raw_img.startswith("http"):
                raw_img = ""
            img, img_src = cache_image(raw_img, referer=page_url)
            out.append({
                "title": title,
                "link": href,
                "date": d,
                "time": "",
                "summary": summary,
                "img": img,
                "imgSrc": img_src,
                "cat": src.get("tag", ""),
                "src": src["name"],
            })
            if len(out) >= PER_WEB:
                break
        if out:
            return out, src["name"], ""

    for m in A_RE.finditer(text):
        href, inner = m.group(1), m.group(2)
        href = urllib.parse.urljoin(page_url, href)
        if urllib.parse.urlparse(href).netloc != host:
            continue
        if any(k in href for k in ("#", "/tag/", "/category/", "/author/", "/page/", "javascript:")):
            continue
        title = clean_text(inner)
        title = WS_RE.sub(" ", title).strip()
        if len(title) < 8 or len(title) > 120:
            continue
        if any(w in title for w in SKIP_WORDS):
            continue
        if href in seen or href.rstrip("/") == page_url.rstrip("/"):
            continue
        seen.add(href)
        out.append({
            "title": title,
            "link": href,
            "date": "",
            "time": "",
            "summary": "",
            "img": "",
            "imgSrc": "",
            "cat": src.get("tag", ""),
            "src": src["name"],
        })
        if len(out) >= PER_WEB:
            break
    return out, src["name"], ""


def load_sources():
    if os.path.exists(SRC_FILE):
        try:
            with open(SRC_FILE, encoding="utf-8") as f:
                s = json.load(f)
            if s:
                return s
        except Exception:
            pass
    return DEFAULT_SRC


def main():
    sources = load_sources()
    all_items, info = [], []
    for src in sources:
        typ = (src.get("type") or "RSS").strip().lower()
        try:
            if typ in ("rss", "atom", "feed"):
                items, ftitle, fdate = rss_items(src)
            elif typ == "webpage":
                items, ftitle, fdate = page_items(src)
            else:
                print("  skip %s (type=%s)" % (src.get("name"), src.get("type")))
                continue
        except Exception as e:
            print("  FAIL %s: %s" % (src.get("name"), str(e)[:110]))
            continue
        print("  %-12s %-8s -> %d 條" % (src.get("name"), typ, len(items)))
        all_items.extend(items)
        info.append({"name": src["name"], "type": src.get("type"), "url": src["url"],
                     "count": len(items), "title": ftitle, "updated": fdate})

    # 去重（同 link 只留第一次）
    seen, uniq = set(), []
    for x in all_items:
        if not x["link"] or x["link"] in seen:
            continue
        seen.add(x["link"])
        uniq.append(x)

    # 有日期的排前面（新→舊），無日期的按抓取次序排在後面
    dated = [x for x in uniq if x["date"]]
    undated = [x for x in uniq if not x["date"]]
    dated.sort(key=lambda x: (x["date"], x["time"]), reverse=True)
    final = (dated + undated)[:LIMIT]

    names = "、".join(i["name"] for i in info) or "政府新聞網"
    payload = {
        "app": "HKBReader",
        "feed": names,
        "feedUrl": info[0]["url"] if info else "",
        "sources": info,
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "feedUpdated": info[0].get("updated") if info else "",
        "count": len(final),
        "items": final,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print("news items=%d (total %d, %d 來源) generated=%s"
          % (payload["count"], len(uniq), len(info), payload["generated"]))
    print("size=%.1f KB" % (os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
