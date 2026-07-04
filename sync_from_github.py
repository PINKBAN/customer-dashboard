import base64, json, os, subprocess

REPO = "PINKBAN/customer-dashboard"
FILES = ["index.html", "contact/客户联络看板.html", "contact/build_dashboard.py"]
BASE = r"c:\Users\asus\Desktop\claude code"

print("正在从 GitHub 拉取最新代码...\n")

for path in FILES:
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{path}?ref=main"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  [{path}] 失败: {result.stderr[:150]}")
        continue

    data = json.loads(result.stdout)
    content_b64 = data.get("content", "")
    if not content_b64:
        print(f"  [{path}] 无内容")
        continue

    content = base64.b64decode(content_b64)
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)

    if os.path.exists(full):
        with open(full, "rb") as f:
            existing = f.read()
        if existing == content:
            print(f"  [{path}] 已是最新")
            continue

    with open(full, "wb") as f:
        f.write(content)
    print(f"  [{path}] 已更新 ({len(content)/1024:.0f} KB)")

print("\n完成！")
