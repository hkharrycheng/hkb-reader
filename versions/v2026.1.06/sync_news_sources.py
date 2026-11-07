# -*- coding: utf-8 -*-
"""
J16 HKBReader - sync_news_sources.py
從飛書「News Feed List」(HIS Tools Base) 抽出 Job ID → J16 的所有來源，
寫成 news-sources.json 供 build_news.py 使用。

用戶在 News Feed List 加了新來源後，重跑本腳本（或 GitHub Actions 內的同一段）即會生效：
    python sync_news_sources.py
    python build_news.py
"""
import json, os, re, subprocess, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "news-sources.json")

BASE_TOKEN = "An0abQoUBalSqJsG66ucDzT3ncg"
TABLE_ID = "tblHXtZC4Dc0RpEQ"
VIEW_ID = "vewFb7ZCho"
J16_REC = "reczz28WRDTbyYuH"          # J16 常數設定記錄（Job ID link 目標）
LINK_RE = re.compile(r"\[(.+?)\]\((https?://.+?)\)")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", shell=True)
    if p.returncode != 0:
        print("CLI FAIL:", (p.stderr or "")[:300])
        sys.exit(1)
    return p.stdout


def main():
    raw = run('lark-cli base +record-list --base-token %s --table-id %s --view-id %s '
              '--format json --limit 200 --as user' % (BASE_TOKEN, TABLE_ID, VIEW_ID))
    doc = json.loads(raw)
    data = doc.get("data", {})
    cols = data.get("fields", [])
    rows = data.get("data", [])

    def idx(name):
        try:
            return cols.index(name)
        except ValueError:
            return None

    i_disp, i_src, i_type, i_job, i_tag = (idx("DisplayName"), idx("Source"),
                                           idx("Source Type"), idx("Job ID"),
                                           idx("Filter用標籤名"))
    out = []
    for r in rows:
        job = r[i_job] if i_job is not None else None
        linked = False
        if isinstance(job, list):
            linked = any((x or {}).get("id") == J16_REC for x in job)
        elif isinstance(job, dict):
            linked = (job.get("id") == J16_REC)
        if not linked:
            continue
        source_txt = (r[i_src] or "") if i_src is not None else ""
        m = LINK_RE.search(source_txt)
        url = (m.group(2) if m else source_txt).strip()
        if not url.startswith("http"):
            continue
        name = ((r[i_disp] or "") if i_disp is not None else "").strip()
        name = re.sub(r"^J\d+-", "", name)
        if not name:
            name = ((r[i_tag] or "") if i_tag is not None else "").strip() or "來源"
        typ = ((r[i_type] or "RSS") if i_type is not None else "RSS").strip()
        out.append({"name": name, "type": typ, "url": url,
                    "tag": ((r[i_tag] or "") if i_tag is not None else "")})

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("news-sources.json: %d 個 J16 來源" % len(out))
    for s in out:
        print("  - %-10s %-8s %s" % (s["name"], s["type"], s["url"]))


if __name__ == "__main__":
    main()
