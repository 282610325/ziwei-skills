#!/usr/bin/env python3
"""前程盘辅助工具。

digest: 从 chart.json 输出前程六宫、完整大限序列与未来三年流年四化。
check : 校验前程报告草稿的结构完整性，并对绝对化表述、收入数字告警。

用法:
    python3 qiancheng.py digest --chart /path/to/chart.json
    python3 qiancheng.py check  --chart /path/to/chart.json --report /path/to/report.draft.md
"""

import argparse
import json
import re
import sys
from pathlib import Path

SIX_PALACES = ["命宫", "官禄", "财帛", "迁移", "田宅", "福德"]
CAREER_LINE = {"官禄", "财帛"}

# 十天干四化（禄、权、科、忌）
SIHUA = {
    "甲": ["廉贞", "破军", "武曲", "太阳"],
    "乙": ["天机", "天梁", "紫微", "太阴"],
    "丙": ["天同", "天机", "文昌", "廉贞"],
    "丁": ["太阴", "天同", "天机", "巨门"],
    "戊": ["贪狼", "太阴", "右弼", "天机"],
    "己": ["武曲", "贪狼", "天梁", "文曲"],
    "庚": ["太阳", "武曲", "太阴", "天同"],
    "辛": ["巨门", "太阳", "文曲", "文昌"],
    "壬": ["天梁", "紫微", "左辅", "武曲"],
    "癸": ["破军", "巨门", "太阴", "贪狼"],
}

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
MOVING_STARS = {"破军", "七杀", "贪狼", "廉贞", "天机", "太阳", "巨门"}
GOOD_STARS = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存"}
MALEFIC_STARS = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}

REQUIRED_HEADINGS = [
    "## 基本信息与口径",
    "## 一句话前程",
    "## 底牌：可行域与不可行域",
    "## 前程六宫速览",
    "## 时间轴：三个大限",
    "### 当前大限",
    "### 下个大限",
    "### 再下个大限",
    "## 未来三年窗口",
    "## 路径选项与代价",
    "## 行动清单",
    "## 不确定性与边界",
]

ABSOLUTE_WORDS = ["必然", "一定会", "必定", "肯定能", "绝对能", "稳赚", "包你", "百分之百", "铁定"]
MONEY_PATTERN = re.compile(r"(年薪|月薪|年收入|月收入|总收入)[^\n]{0,8}\d")


def year_ganzhi(year: int):
    return STEMS[(year - 4) % 10] + BRANCHES[(year - 4) % 12]


def load_chart(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def palace_by_name(chart: dict, name: str):
    for p in chart["natal"]["palaces"]:
        if p["name"] == name:
            return p
    return None


def palace_by_branch(chart: dict, branch: str):
    for p in chart["natal"]["palaces"]:
        if p["earthlyBranch"] == branch:
            return p
    return None


def star_names(palace: dict):
    return [s["name"] for s in palace.get("majorStars", [])] + [
        s["name"] for s in palace.get("minorStars", [])
    ]


def grade(palace: dict) -> str:
    """单宫粗判：强 / 中 / 弱。只做提示，最终以报告人工判断为准。"""
    majors = palace.get("majorStars", [])
    minors = palace.get("minorStars", [])
    if not majors:
        return "中(空宫,借对宫)"
    malefic = [s for s in minors if s["name"] in MALEFIC_STARS]
    has_ji = any(s.get("mutagen") == "忌" for s in majors)
    weak_bright = any(s.get("brightness") in {"陷", "平"} for s in majors)
    good_bright = any(s.get("brightness") in {"庙", "旺"} for s in majors)
    if has_ji or len(malefic) >= 2 or (weak_bright and len(malefic) >= 1):
        return "弱"
    if good_bright and not malefic:
        return "强"
    return "中"


def decadal_hint(chart: dict, item: dict) -> str:
    """按本技能四档定义做粗判，仅作提示。"""
    stem = item["heavenlyStem"]
    sihua = SIHUA[stem]
    landed = {}
    for mutagen, star in zip(["禄", "权", "科", "忌"], sihua):
        pal = next(
            (p["name"] for p in chart["natal"]["palaces"] if star in star_names(p)), None
        )
        landed[mutagen] = (star, pal)

    name = item["palaceName"]
    if landed["忌"][1] in CAREER_LINE:
        return "收缩期"
    if name in {"官禄", "财帛", "命宫"} and (
        landed["禄"][1] in CAREER_LINE or landed["权"][1] in CAREER_LINE
    ):
        return "发力期"
    pal = palace_by_name(chart, name)
    if name in {"迁移", "子女", "夫妻"} and pal and MOVING_STARS & set(star_names(pal)):
        return "转型期"
    return "铺路期"


def fmt_palace_line(chart: dict, p: dict) -> str:
    majors = "、".join(
        f"{s['name']}({s.get('brightness') or '未提供'}{'/' + s['mutagen'] if s.get('mutagen') else ''})"
        for s in p.get("majorStars", [])
    ) or "空宫"
    malefic = [s["name"] for s in p.get("minorStars", []) if s["name"] in MALEFIC_STARS]
    soft = [s["name"] for s in p.get("minorStars", []) if s["name"] in GOOD_STARS]
    return (
        f"{p['name']:<3} {p['heavenlyStem']}{p['earthlyBranch']}  "
        f"主星: {majors:<28} 煞: {'、'.join(malefic) or '无':<8} "
        f"吉辅: {'、'.join(soft) or '无':<10} 判定提示: {grade(p)}"
    )


def digest(chart: dict):
    natal = chart["natal"]
    identity = chart.get("identity", {})
    time_info = chart.get("time", {})
    print("=== 基本信息 ===")
    print(f"姓名: {identity.get('name')}  性别: {natal.get('gender')}")
    print(f"公历: {time_info.get('civil_birth_date')} {time_info.get('civil_birth_time')}  "
          f"误差±{time_info.get('uncertainty_minutes')}分钟  时辰索引: {time_info.get('time_index')}")
    print(f"五行局: {natal.get('fiveElementsClass')}  命主: {natal.get('soul')}  身主: {natal.get('body')}")
    for w in time_info.get("warnings", []):
        print(f"警告: {w}")

    print("\n=== 前程六宫 ===")
    for name in SIX_PALACES:
        p = palace_by_name(chart, name)
        if p:
            print(fmt_palace_line(chart, p))

    print("\n=== 三方四正 ===")
    surrounded = chart.get("surrounded_palaces", {})
    for name in SIX_PALACES:
        s = surrounded.get(name)
        if s:
            print(
                f"{name:<3} → 对宫 {s['opposite']['name']:<3}"
                f"/ 财帛位 {s['wealth']['name']:<3}/ 官禄位 {s['career']['name']}"
            )

    print("\n=== 六宫宫干飞化 ===")
    flights = chart.get("transformations", {}).get("palace_flights", [])
    for name in SIX_PALACES:
        p = palace_by_name(chart, name)
        rows = [f for f in flights if f.get("source_palace") == name]
        parts = []
        for f in rows:
            target = "本宫(自化)" if f.get("self_mutagen") else f["natal_palace"]
            parts.append(f"{f['star']}化{f['mutagen']}→{target}")
        print(f"{name}({p['heavenlyStem']}): {'；'.join(parts) if parts else '无飞化'}")

    print("\n=== 大限序列（当前 + 后两个）===")
    items = chart["fortune"]["decadal_list"]
    current = chart["fortune"]["current_decadal"]
    idx = next((i for i, d in enumerate(items) if d["ageRange"] == current["ageRange"]), 0)
    child_limit = current["ageRange"][0] < 15
    if child_limit:
        print("尚未进入首个大限（童限）：本盘只做可行域，不做档位与流年窗口。")
    for item in items[idx: idx + 3]:
        stem = item["heavenlyStem"]
        landed = "、".join(
            f"{m}{star}→{next((q['name'] for q in natal['palaces'] if star in star_names(q)), '未落宫')}"
            for m, star in zip(["禄", "权", "科", "忌"], SIHUA[stem])
        )
        tier = "童限(不判档)" if item["ageRange"][0] < 15 else decadal_hint(chart, item)
        mark = " ← 当前" if item["ageRange"] == current["ageRange"] else ""
        print(
            f"{item['ageRange'][0]:>3}-{item['ageRange'][1]:<3}虚岁 "
            f"{item['yearRange'][0]}-{item['yearRange'][1]}  "
            f"大限命宫: {item['palaceName']:<3}({stem})  {landed}  "
            f"档位提示: {tier}{mark}"
        )

    print("\n=== 流年四化（分析年 + 后两年）===")
    start = int(str(chart["fortune"]["analysis_date"])[:4])
    for year in range(start, start + 3):
        gz = year_ganzhi(year)
        stem, branch = gz[0], gz[1]
        ming = palace_by_branch(chart, branch)
        landed = "、".join(
            f"{m}{star}→{next((q['name'] for q in natal['palaces'] if star in star_names(q)), '未落宫')}"
            for m, star in zip(["禄", "权", "科", "忌"], SIHUA[stem])
        )
        print(
            f"{year} {gz}年  流年命宫叠本命: {ming['name'] if ming else '未定位'}  {landed}"
        )

    print("\n注：档位与强弱均为脚本粗判，只能作为提示；报告须写明依据自行判定。")


def check(chart: dict, report_path: str) -> int:
    text = Path(report_path).read_text(encoding="utf-8")
    errors, warnings = [], []

    for h in REQUIRED_HEADINGS:
        if h not in text:
            errors.append(f"缺少必填标题: {h}")

    for key in ("PERSON_ID", "VERSION", "CHART_SHA256"):
        if key not in text:
            errors.append(f"报告头缺少 {key}")

    path_heads = re.findall(r"^###\s*路径\s*\S+", text, flags=re.M)
    if len(path_heads) < 3:
        errors.append(f"路径选项不足三条（当前 {len(path_heads)} 条）；只给一条等于替用户做决定")

    section = re.search(r"## 前程六宫速览(.*?)(?=\n## )", text, flags=re.S)
    if section:
        missing = [n for n in SIX_PALACES if n not in section.group(1)]
        if missing:
            errors.append(f"前程六宫速览缺少: {'、'.join(missing)}")

    decadals = chart["fortune"]["decadal_list"]
    current = chart["fortune"]["current_decadal"]
    idx = next((i for i, d in enumerate(decadals) if d["ageRange"] == current["ageRange"]), 0)
    for item in decadals[idx: idx + 3]:
        y0, y1 = item["yearRange"]
        if not any(str(y0) in line and str(y1) in line for line in text.splitlines()):
            errors.append(f"大限序列缺少年份区间 {y0}-{y1}（{item['palaceName']}）")

    start = int(str(chart["fortune"]["analysis_date"])[:4])
    for year in range(start, start + 3):
        if str(year) not in text:
            errors.append(f"未来三年窗口缺少 {year} 年")

    for w in ABSOLUTE_WORDS:
        if w in text:
            warnings.append(f"绝对化表述: {w}")
    for m in MONEY_PATTERN.finditer(text):
        warnings.append(f"疑似给出收入数字: {m.group(0)}")

    print(f"报告: {report_path}")
    print(f"大限档位覆盖: {decadals[idx]['ageRange']} / {decadals[min(idx+1, len(decadals)-1)]['ageRange']} / {decadals[min(idx+2, len(decadals)-1)]['ageRange']}")
    for e in errors:
        print(f"[FAIL] {e}")
    for w in warnings:
        print(f"[WARN] {w}")
    if errors:
        print("\n结论: 未通过，先修草稿再交付。")
        return 1
    print("\n结论: 结构校验通过。这不等于解释正确，仍需人工核对星曜与四化出处。")
    return 0


def main():
    parser = argparse.ArgumentParser(description="前程盘辅助工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("digest", help="输出前程相关结构化摘要")
    d.add_argument("--chart", required=True)

    c = sub.add_parser("check", help="校验报告草稿结构")
    c.add_argument("--chart", required=True)
    c.add_argument("--report", required=True)

    args = parser.parse_args()
    chart = load_chart(args.chart)

    if args.cmd == "digest":
        digest(chart)
        return 0
    return check(chart, args.report)


if __name__ == "__main__":
    sys.exit(main())
