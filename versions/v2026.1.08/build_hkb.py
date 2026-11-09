# -*- coding: utf-8 -*-
"""
J16 HKBReader - build hkb.json from HKB Bitable dumps + OneDrive DOCX map
Input : _raw/hkbu.ndjson (HKB單元), _raw/hkb3.ndjson (HKB標題3),
        _raw/hkb4.ndjson (HKB標題4), _raw/hkbl.ndjson (HKB Links),
        _raw/docxmap.json (DOCX 檔名 -> OneDrive 分類資料夾)
Output: hkb.json
"""
import json, os, sys, datetime, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE_DIR, "_raw")
OUT = os.path.join(BASE_DIR, "hkb.json")
VERSION = "2026.1.08"

FOLDER_ORDER = [
    "Academics and Workplace", "Business and Economics", "Computer Science",
    "Creative Media", "Human History and Government", "Medic and Health",
    "Philosophy and Anthropology", "Science and Technology",
    "Social Science", "Space and Environment",
]
UNSORTED = "未分類"


def load_ndjson(name):
    path = os.path.join(RAW, name)
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def s(v):
    """cell -> str"""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "、".join(s(x) for x in v)
    if isinstance(v, dict):
        return s(v.get("text") or v.get("name") or v.get("link") or "")
    return str(v)


def norm_doc(name):
    """學科名正規化：統一空白、去掉檔名式的「 - 」，令 Base 舊名／磁碟新名可以對上"""
    t = re.sub(r"\s+", " ", str(name or "")).strip()
    t = t.replace(" - ", " ")
    return t.lower()


def link_id(v):
    """link cell -> first id"""
    if isinstance(v, list) and v:
        first = v[0]
        if isinstance(first, dict):
            return first.get("id") or ""
    return ""


def link_ids(v):
    if isinstance(v, list):
        return [x.get("id") for x in v if isinstance(x, dict) and x.get("id")]
    return []


MEDIA_MAP = {
    "am730.com.hk": "am730",
    "unwire.hk": "unwire.hk",
    "hket.com": "香港經濟日報",
    "stheadline.com": "星島頭條",
    "msn.com": "MSN",
    "yahoo.com": "Yahoo 新聞",
    "thenewslens.com": "關鍵評論網",
    "kaiak.tw": "kaiak.tw",
    "cmoneylearning.com.tw": "CMoney",
    "sina.com.cn": "新浪財經",
    "36kr.com": "36Kr",
    "thinkhk.com": "ThinkHK",
    "thewitnesshk.com": "法庭線",
    "doubaocdn.com": "截圖",
    "doubao.com": "截圖",
}


def norm_media(v):
    """來源 -> 媒體名；URL 取網域對應品牌，截圖類統一歸「截圖／帖文」"""
    t = s(v).strip()
    if not t:
        return ""
    low = t.lower()
    if low.startswith("http"):
        host = low.split("//", 1)[-1].split("/")[0].split("?")[0]
        host = host.replace("www.", "")
        for key, brand in MEDIA_MAP.items():
            if key in host:
                return brand
        return host
    if "截圖" in t or "帖文" in t:
        return "截圖／帖文"
    return t


def norm_author(v):
    """作者 -> 去掉括號內職銜／任職機構"""
    t = s(v).strip()
    if not t:
        return ""
    return re.split(r"[（(]", t)[0].strip() or t


IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def img_list(cell):
    """attachment cell -> [{token, file, name}]"""
    out = []
    for x in (cell or []):
        if not isinstance(x, dict):
            continue
        tok = x.get("file_token")
        if not tok:
            continue
        name = x.get("name") or ""
        ext = os.path.splitext(name)[1].lower()
        if ext not in IMG_EXT:
            ext = ".jpg"
        out.append({"token": tok, "file": "images/" + tok + ext, "name": name})
    return out


def parse_dt(v):
    """date-ish cell -> 'YYYY-MM-DD HH:MM' (sortable string), '' if none"""
    if v is None or v == "":
        return ""
    if isinstance(v, (int, float)):
        try:
            ts = float(v) / 1000.0
            return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return ""
    t = str(v).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S",
                "%Y/%m/%d %H:%M", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            # python 3.11 handles %z with colon; strip ':' in offset for old styles
            return datetime.datetime.strptime(t, fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    # fallback: take leading 16 chars of iso
    if len(t) >= 16 and t[4] == "-" and t[7] == "-":
        return (t[:10] + " " + t[11:16]).replace("T", " ")
    return ""


def main():
    units_raw = load_ndjson("hkbu.ndjson")
    t3_raw = load_ndjson("hkb3.ndjson")
    t4_raw = load_ndjson("hkb4.ndjson")
    links_raw = load_ndjson("hkbl.ndjson")

    docmap = {}
    docmap_path = os.path.join(RAW, "docxmap.json")
    if os.path.exists(docmap_path):
        with open(docmap_path, "r", encoding="utf-8-sig") as f:
            rows = json.load(f)
        for r in rows:
            name = r.get("name") or ""
            folder = r.get("folder") or ""
            key = norm_doc(name)
            if key and key not in docmap:
                docmap[key] = {"name": name, "folder": folder, "rel": r.get("rel") or ""}

    # ---------- t4 ----------
    t4 = []
    for r in t4_raw:
        t4.append({
            "id": r.get("record_id", ""),
            "name": s(r.get("標題4")) or s(r.get("DisplayName")),
            "t3": link_id(r.get("標題3")),
            "text": s(r.get("文字詳細")),
            "textFormula": s(r.get("文字")),
            "pro": s(r.get("正面證據")),
            "con": s(r.get("反面證據")),
            "comment": s(r.get("評論")),
            "fact": s(r.get("Fact總評%")),
            "factNum": r.get("FACT總評%"),
            "aiPct": r.get("AI看法%"),
            "lie": s(r.get("謊言類型")) or s(r.get("谎言的类型")),
            "table": s(r.get("表格詳細")),
            "source": s(r.get("原文SOURCE")),
            "author": s(r.get("原文作者")),
            "region": s(r.get("原文地區背景")),
            "artDate": s(r.get("文章日期")),
            "reqDate": s(r.get("要求日期")),
            "imgs": img_list(r.get("圖片")),
            "updated": parse_dt(r.get("內容最後更新")),
        })
    t4_by_id = {x["id"]: x for x in t4}
    t4_by_t3 = {}
    for x in t4:
        t4_by_t3.setdefault(x["t3"], []).append(x)

    # ---------- links ----------
    links = []
    for r in links_raw:
        links.append({
            "id": r.get("record_id", ""),
            "title": s(r.get("Link 標題")) or s(r.get("DisplayName")),
            "url": s(r.get("Link")),
            "t3": link_id(r.get("標題3")),
        })
    links_by_t3 = {}
    for x in links:
        links_by_t3.setdefault(x["t3"], []).append(x)

    # ---------- t3 ----------
    t3 = []
    t3_by_id = {}
    for r in t3_raw:
        rec = {
            "id": r.get("record_id", ""),
            "name": s(r.get("標題3")) or s(r.get("DisplayName")),
            "unit": link_id(r.get("HKB單元")),
            "text": s(r.get("文字詳細")),
            "updated": parse_dt(r.get("內容最後更新")),
            "lastDocx": parse_dt(r.get("最後更新DOCX")),
            "imgs": img_list(r.get("標題3圖片")),
            "t4ids": link_ids(r.get("標題4")),
        }
        rec["kind"] = "article" if rec["t4ids"] else "knowledge"
        t3.append(rec)
        t3_by_id[rec["id"]] = rec

    # ---------- units ----------
    docs = {}
    units = []
    for r in units_raw:
        doc_raw = s(r.get("HKB Documentation"))
        hit = docmap.get(norm_doc(doc_raw))
        # 顯示用新名（磁碟 DOCX 檔名），唔再用 Base 可能殘留嘅舊名
        doc = hit["name"] if hit else doc_raw
        folder = (hit or {}).get("folder") or UNSORTED
        rec = {
            "id": r.get("record_id", ""),
            "t1": s(r.get("標題1")),
            "t2": s(r.get("標題2")),
            "doc": doc,
            "folder": folder,
            "display": s(r.get("DisplayName")),
            "docxAt": parse_dt(r.get("最後DOCX更新")),
            "imgs": img_list(r.get("標題2圖片")),
            "t3ids": link_ids(r.get("標題3")),
        }
        units.append(rec)
        if doc:
            d = docs.setdefault(doc, {
                "doc": doc, "folder": folder, "units": 0, "t3": 0, "t4": 0, "last": "",
                "rel": (hit or {}).get("rel") or "",
            })
            d["units"] += 1

    units_by_id = {u["id"]: u for u in units}

    # attach t3 -> unit info, compute dates
    for rec in t3:
        u = units_by_id.get(rec["unit"])
        rec["t1"] = u["t1"] if u else ""
        rec["t2"] = u["t2"] if u else ""
        rec["doc"] = u["doc"] if u else ""
        rec["folder"] = u["folder"] if u else UNSORTED
        rec["t4count"] = len(rec["t4ids"])
        rec["last"] = max(rec["updated"], rec["lastDocx"])
        kids = t4_by_t3.get(rec["id"], [])
        for k in kids:
            if k["updated"] and k["updated"] > rec["last"]:
                rec["last"] = k["updated"]
        rec["media"] = sorted({norm_media(k["source"]) for k in kids} - {""})
        rec["auts"] = sorted({norm_author(k["author"]) for k in kids} - {""})
        # 科普 vs 相關文章：有外部來源／作者（原文SOURCE／原文作者）＝相關文章；否則屬自寫知識（科普）
        rec["kind"] = "article" if (rec["media"] or rec["auts"]) else "knowledge"
        if rec["doc"] and rec["doc"] in docs:
            docs[rec["doc"]]["t3"] += 1
            docs[rec["doc"]]["t4"] += rec["t4count"]
            if rec["last"] and rec["last"] > docs[rec["doc"]]["last"]:
                docs[rec["doc"]]["last"] = rec["last"]
        if rec["doc"]:
            if not rec["last"]:
                pass

    # unit-level derived last update (docx + children)
    for u in units:
        last = u["docxAt"]
        for tid in u["t3ids"]:
            t = t3_by_id.get(tid)
            if t and t["last"] and t["last"] > last:
                last = t["last"]
        u["last"] = last
        u["t3count"] = len(u["t3ids"])
        u["t4count"] = sum(t3_by_id[tid]["t4count"] for tid in u["t3ids"] if tid in t3_by_id)

    # ---------- 標題1 groups ----------
    groups = {}
    for u in units:
        key = (u["doc"] or "") + "||" + (u["t1"] or "")
        g = groups.setdefault(key, {
            "key": key, "t1": u["t1"], "doc": u["doc"], "folder": u["folder"],
            "units": [], "t3": 0, "t4": 0, "last": "",
        })
        g["units"].append(u["id"])
        g["t3"] += u["t3count"]
        g["t4"] += u["t4count"]
        if u["last"] and u["last"] > g["last"]:
            g["last"] = u["last"]
    group_list = []
    for g in groups.values():
        group_list.append({
            "key": g["key"], "t1": g["t1"], "doc": g["doc"], "folder": g["folder"],
            "units": g["units"], "unitCount": len(g["units"]),
            "t3": g["t3"], "t4": g["t4"], "last": g["last"],
            "cover": "",
        })
        # cover image: first unit thumbnail, else first t3 image
        for uid in g["units"]:
            uu = units_by_id.get(uid)
            if uu and uu["imgs"]:
                group_list[-1]["cover"] = uu["imgs"][0]["file"]
                break
        if not group_list[-1]["cover"]:
            for uid in g["units"]:
                uu = units_by_id.get(uid)
                for tid in (uu["t3ids"] if uu else []):
                    tt = t3_by_id.get(tid)
                    if tt and tt["imgs"]:
                        group_list[-1]["cover"] = tt["imgs"][0]["file"]
                        break
                if group_list[-1]["cover"]:
                    break
    group_list.sort(key=lambda x: (x["last"] or "", x["t1"]), reverse=True)

    # ---------- folders ----------
    folder_rows = []
    names = list(FOLDER_ORDER)
    for f in {u["folder"] for u in units}:
        if f not in names:
            names.append(f)
    for name in names:
        fu = [u for u in units if u["folder"] == name]
        name_t3 = [t for t in t3 if t["folder"] == name]
        docx_count = sum(1 for v in docmap.values() if v["folder"] == name)
        last = max([u["last"] for u in fu] + [""])
        folder_rows.append({
            "folder": name,
            "docx": docx_count,
            "units": len(fu),
            "t3": len(name_t3),
            "t4": sum(t["t4count"] for t in name_t3),
            "articles": sum(1 for t in name_t3 if t["kind"] == "article"),
            "knowledge": sum(1 for t in name_t3 if t["kind"] == "knowledge"),
            "docs": sorted({u["doc"] for u in fu}),
            "last": last,
        })

    payload = {
        "app": "HKBReader",
        "version": VERSION,
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "counts": {
            "folders": len([f for f in folder_rows if f["units"] > 0]),
            "allFolders": len(folder_rows),
            "docx": len(docmap),
            "docs": len(docs),
            "units": len(units),
            "t3": len(t3),
            "t4": len(t4),
            "links": len(links),
        },
        "folders": folder_rows,
        "docs": sorted(docs.values(), key=lambda x: x["doc"]),
        "units": units,
        "t3": t3,
        "t4": t4,
        "links": links,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    # ---------- image download plan ----------
    plan = []
    for u in units:
        for im in u["imgs"]:
            plan.append({"table": "tblnFQMtxZvARqen", "record": u["id"], "token": im["token"],
                         "file": im["file"], "name": im["name"], "field": "標題2圖片"})
    for t in t3:
        for im in t["imgs"]:
            plan.append({"table": "tbli6dtCgJAxgrlP", "record": t["id"], "token": im["token"],
                         "file": im["file"], "name": im["name"], "field": "標題3圖片"})
    for k in t4:
        for im in k["imgs"]:
            plan.append({"table": "tbl2kp5TPHaqUj0i", "record": k["id"], "token": im["token"],
                         "file": im["file"], "name": im["name"], "field": "圖片"})
    with open(os.path.join(RAW, "images.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)

    # ---------- console report ----------
    print("units=%d t3=%d t4=%d links=%d docs=%d" % (len(units), len(t3), len(t4), len(links), len(docs)))
    print("docx files mapped=%d" % len(docmap))
    missing = [d for d in docs if norm_doc(d) not in docmap and d]
    print("HKB docs without local DOCX: %s" % (missing if missing else "none"))
    for f in folder_rows:
        print("  %-32s docx=%-4d units=%-3d t3=%-3d t4=%-3d last=%s" %
              (f["folder"], f["docx"], f["units"], f["t3"], f["t4"], f["last"]))
    print("size=%.1f KB" % (os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
