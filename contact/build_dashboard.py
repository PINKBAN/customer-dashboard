#!/usr/bin/env python3
"""
客户联络看板 — 一键更新脚本
用法: python build_dashboard.py [销售数据.xlsx] [客户联络.xlsx]
输出: index.html (根目录) + 客户联络看板.html (contact/)
"""

import sys, os, json, math, re
from datetime import datetime, date, timedelta
from collections import defaultdict
import numpy as np
import openpyxl

# ---- 配置 ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_HTML = os.path.join(ROOT, "index.html")
OUTPUT_HTML = os.path.join(ROOT, "index.html")
OUTPUT_HTML2 = os.path.join(ROOT, "contact", "客户联络看板.html")
SUPABASE_URL = "https://rmuhugjufmoghzyynvrb.supabase.co"
SUPABASE_KEY = "sb_publishable_sv9TseWVsQ6dhkqnPYbiqw_aW1Df-5D"

# ---- 工具 ----
def parse_date(val):
    """解析各种日期格式"""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if not val:
        return None
    s = str(val).strip()
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # 尝试只取前10个字符
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None

# ---- 加载数据 ----
def load_customers(filepath):
    """加载客户联络表"""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    customers = []
    for row in rows:
        if not row[0]:
            continue
        contact = str(row[10] or "").strip()
        tags = str(row[16] or "").strip()
        # 清理标签中的多余逗号
        tags = ",".join(t for t in tags.replace("，", ",").split(",") if t.strip())
        customers.append({
            "name": str(row[0]).strip(),
            "manager": str(row[1] or "").strip(),
            "lastTradeDate": parse_date(row[3]) or parse_date(row[2]),
            "lastAmount": float(row[5] or 0),
            "receivable": float(row[6] or 0),
            "yearAmount": float(row[7] or 0),
            "monthAmount": float(row[8] or 0),
            "lastMonthAmount": float(row[11] or 0),
            "contact": contact,
            "level": int(row[13] or 0),
            "payment": float(row[15] or 0),
            "tags": tags,
            "noTradeDays": int(row[4] or 0),
        })
    return customers

def load_sales(filepath):
    """加载销售明细表，返回 {客户名: [日期列表]}"""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    customer_dates = defaultdict(list)
    for row in rows:
        name = str(row[1] or "").strip()
        if not name:
            continue
        d = parse_date(row[0])
        if d:
            customer_dates[name].append(d)
    return customer_dates

# ---- 周期分析 ----
def analyze_cycle(dates, today):
    """分析客户的拿货周期，返回周期分析结果"""
    if len(dates) < 2:
        return {
            "hasCycle": False,
            "cycleDays": 0,
            "regularity": 0,
            "predictedNext": "",
            "daysToNext": 0,
            "cycleLastDate": "",
            "cycleUrgency": "normal",
            "suggestion": "近期有交易，暂无周期数据"
        }

    # 排序去重
    unique_dates = sorted(set(dates))
    if len(unique_dates) < 2:
        return {
            "hasCycle": False,
            "cycleDays": 0,
            "regularity": 0,
            "predictedNext": "",
            "daysToNext": 0,
            "cycleLastDate": "",
            "cycleUrgency": "normal",
            "suggestion": "近期有交易，暂无周期数据"
        }

    # 计算间隔
    intervals = []
    for i in range(1, len(unique_dates)):
        delta = (unique_dates[i] - unique_dates[i-1]).days
        if delta > 0:
            intervals.append(delta)

    if not intervals:
        return {
            "hasCycle": False,
            "cycleDays": 0,
            "regularity": 0,
            "predictedNext": "",
            "daysToNext": 0,
            "cycleLastDate": "",
            "cycleUrgency": "normal",
            "suggestion": "近期有交易，暂无周期数据"
        }

    intervals_arr = np.array(intervals)
    median_cycle = round(float(np.median(intervals_arr)), 1)

    # 规律性: 1 - CV (变异系数)，限制在0-1
    mean_cycle = float(np.mean(intervals_arr))
    if mean_cycle > 0:
        cv = float(np.std(intervals_arr)) / mean_cycle
        regularity = round(max(0, min(1, 1 - cv)), 2)
    else:
        regularity = 0

    # 最近一次交易
    last_date = unique_dates[-1]

    # 预测下次拿货日期
    predicted_next = last_date + timedelta(days=int(median_cycle))
    days_to_next = (predicted_next - today).days

    # 紧急程度
    overdue_threshold = int(median_cycle * 0.5) if median_cycle > 0 else 7
    if days_to_next < -14:
        urgency = "urgent"      # 超期>14天
    elif days_to_next < 0:
        urgency = "overdue"     # 已超期
    elif days_to_next <= 3:
        urgency = "soon"         # 3天内
    elif days_to_next <= 7:
        urgency = "upcoming"     # 一周内
    else:
        urgency = "normal"

    # 建议文本
    if urgency == "urgent":
        suggestion = f"已超期{abs(days_to_next)}天，需立即联系"
    elif urgency == "overdue":
        suggestion = f"刚超期{abs(days_to_next)}天，建议本周联系"
    elif urgency == "soon":
        suggestion = f"预计{days_to_next}天后到拿货周期，建议提前联系"
    elif urgency == "upcoming":
        suggestion = f"距拿货周期还有{days_to_next}天"
    else:
        suggestion = f"距拿货周期还有{days_to_next}天"

    return {
        "hasCycle": True,
        "cycleDays": median_cycle,
        "regularity": regularity,
        "predictedNext": predicted_next.strftime("%Y-%m-%d"),
        "daysToNext": days_to_next,
        "cycleLastDate": last_date.strftime("%Y-%m-%d"),
        "cycleUrgency": urgency,
        "suggestion": suggestion
    }

# ---- 匹配客户 ----
def match_customers(customer_list, sales_dict):
    """将销售数据中的日期匹配到客户（支持模糊匹配）"""
    # 建立名字到日期的映射
    name_to_dates = {}
    for cname, dates in sales_dict.items():
        name_to_dates[cname] = dates

    # 对每个客户尝试精确匹配和模糊匹配
    for c in customer_list:
        cname = c["name"]
        if cname in name_to_dates and len(name_to_dates[cname]) >= 2:
            c["_dates"] = name_to_dates[cname]
            continue
        # 尝试模糊匹配
        found = False
        for sname, dates in name_to_dates.items():
            # 包含匹配
            if cname in sname or sname in cname:
                if len(dates) >= 2 and not found:
                    c["_dates"] = dates
                    found = True
        if not found:
            c["_dates"] = name_to_dates.get(cname, [])

def build_full_data(customer_list, today):
    """构建 FULL_DATA"""
    result = []
    for i, c in enumerate(customer_list):
        cycle = analyze_cycle(c.get("_dates", []), today)
        item = {
            "id": i,
            "name": c["name"],
            "manager": c["manager"],
            "lastTradeDate": c["lastTradeDate"].strftime("%Y-%m-%d") if c["lastTradeDate"] else "",
            "noTradeDays": c["noTradeDays"],
            "lastAmount": c["lastAmount"],
            "receivable": c["receivable"],
            "yearAmount": c["yearAmount"],
            "monthAmount": c["monthAmount"],
            "lastMonthAmount": c["lastMonthAmount"],
            "contact": c["contact"],
            "level": c["level"],
            "payment": c["payment"],
            "tags": c["tags"],
            **cycle
        }
        result.append(item)
    return result

# ---- 生成 HTML ----
def generate_html(full_data, template_path, today):
    """将 FULL_DATA 注入到 HTML 模板中"""
    # 读取现有模板
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 更新数据截止日期
    date_str = today.strftime("%Y-%m-%d")
    html = re.sub(
        r'数据截止：\d{4}-\d{2}-\d{2}',
        f'数据截止：{date_str}',
        html
    )

    # 替换 FULL_DATA（找到 var FULL_DATA = [...] 并替换）
    json_str = json.dumps(full_data, ensure_ascii=False, separators=(",", ": "))
    new_line = f"var FULL_DATA = {json_str};"

    # 使用正则找到并替换整行
    pattern = r'var FULL_DATA = \[.*?\];'
    html = re.sub(pattern, new_line.replace('\\', '\\\\'), html, count=1)

    return html

# ---- 主流程 ----
def main():
    today = date.today()
    print(f"=== 客户联络看板 — 数据更新 ===")
    print(f"日期: {today}")

    # 客户联络文件：优先使用最新日期的版本
    contact_dir = os.path.join(ROOT, "contact")
    contact_file = os.path.join(contact_dir, "客户联络.xlsx")
    # 如果有更新的客户联络文件（如5.23.xlsx这种18列的），自动使用
    for f in sorted(os.listdir(contact_dir), reverse=True):
        fpath = os.path.join(contact_dir, f)
        if f.endswith('.xlsx') and f != '客户联络.xlsx' and os.path.getsize(fpath) < 500_000:
            # 检查是否是客户联络表（18列）
            try:
                wb = openpyxl.load_workbook(fpath, data_only=True)
                ws = wb.active
                if ws.max_column == 18 and ws.max_row < 2000:
                    contact_file = fpath
                    print(f"自动选择最新客户联络: {os.path.basename(contact_file)}")
                    wb.close()
                    break
                wb.close()
            except:
                pass

    if len(sys.argv) > 1:
        sales_file = sys.argv[1]
        if not os.path.isabs(sales_file):
            sales_file = os.path.join(contact_dir, sales_file)
    else:
        # 自动找最新的销售数据文件（大文件>500KB），排除客户联络表（小文件）
        xlsx_files = []
        for f in os.listdir(contact_dir):
            if f.endswith('.xlsx') and '客户联络' not in f:
                fpath = os.path.join(contact_dir, f)
                # 销售数据文件通常 > 1MB，客户联络表 < 500KB
                if os.path.getsize(fpath) > 500_000:
                    xlsx_files.append((os.path.getmtime(fpath), fpath))
        if xlsx_files:
            xlsx_files.sort(reverse=True)
            sales_file = xlsx_files[0][1]
            print(f"自动选择最新销售文件: {os.path.basename(sales_file)}")
        else:
            print("错误: 未找到销售数据文件（>500KB的xlsx），请放入 contact 文件夹")
            sys.exit(1)

    print(f"销售数据: {sales_file}")
    print(f"客户联络: {contact_file}")

    # 加载数据
    print("\n[1/4] 加载客户联络表...")
    customers = load_customers(contact_file)
    print(f"  客户数: {len(customers)}")

    print("[2/4] 加载销售明细...")
    sales = load_sales(sales_file)
    # 按日期数排序显示top客户
    top = sorted(sales.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print(f"  有销售记录客户数: {len(sales)}")
    print(f"  Top5: {[(n, len(d)) for n, d in top]}")

    print("[3/4] 匹配客户 + 计算周期...")
    match_customers(customers, sales)
    full_data = build_full_data(customers, today)

    # 统计
    with_cycle = sum(1 for d in full_data if d["hasCycle"])
    urgent = sum(1 for d in full_data if d["cycleUrgency"] == "urgent")
    overdue = sum(1 for d in full_data if d["cycleUrgency"] == "overdue")
    print(f"  总客户: {len(full_data)}")
    print(f"  有周期数据: {with_cycle}")
    print(f"  紧急(超期>14天): {urgent}")
    print(f"  超期: {overdue}")

    print("[4/4] 生成 HTML...")

    # 确保模板存在
    if not os.path.exists(TEMPLATE_HTML):
        print(f"  错误: 模板文件不存在 {TEMPLATE_HTML}")
        sys.exit(1)

    html = generate_html(full_data, TEMPLATE_HTML, today)

    # 写入文件
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  -> {OUTPUT_HTML}")

    with open(OUTPUT_HTML2, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  -> {OUTPUT_HTML2}")

    print("\n完成! 可以提交到 GitHub:")
    print('  git add index.html "contact/客户联络看板.html"')
    print(f'  git commit -m "数据更新 {today}"')
    print("  git push origin main")

if __name__ == "__main__":
    main()
