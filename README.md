# 客户联络管理看板

多人协作的客户联络管理工具，支持跨网络实时数据同步。

## 架构

```
Excel 数据 → build_dashboard.py → Supabase (data_snapshots)
                                      ↓
浏览器 ← index.html ← Supabase API ← 任何网络环境
                                      ↓
勾选/原因 → Supabase (customer_state) ← 实时共享
```

- **基础数据**（客户列表、拿货周期）存储在 Supabase `data_snapshots` 表，页面加载时拉取
- **协作状态**（勾选、原因、今日交易）存储在 Supabase `customer_state` 表，实时同步
- 不再需要每次更新数据后重新部署 HTML

## 快速开始

### 1. 初始化 Supabase（仅首次）

在 Supabase SQL Editor 中执行 `contact/supabase_init.sql`

### 2. 配置连接

修改根目录 `config.js` 中的 Supabase URL 和 Key

### 3. 导入数据

```bash
cd contact
pip install -r requirements.txt

# 将 Excel 文件放入 contact/ 文件夹，然后：
python build_dashboard.py
```

脚本会自动识别最新的销售明细表（大文件）和客户联络表（18列），计算拿货周期后将数据上传到 Supabase。

### 4. 启动服务器

**Mac/Linux:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

**手动启动:**
```bash
cd contact
python server.py --prod
```

访问 `http://localhost:5000`

### 5. 部署到云端（可选）

将整个文件夹部署到任意静态服务器（Vercel、Netlify、Nginx 等），或直接使用 Supabase 的静态托管。所有员工通过同一个 URL 访问即可。

## 文件结构

```
customer-dashboard/
├── index.html              # 主页面（从 Supabase 加载数据）
├── config.js               # Supabase 配置（唯一配置入口）
├── start.sh                # Mac/Linux 启动脚本
├── contact/
│   ├── server.py           # 静态文件服务器
│   ├── build_dashboard.py  # Excel → Supabase 数据更新脚本
│   ├── start.bat           # Windows 启动脚本
│   ├── supabase_init.sql   # 数据库初始化 SQL
│   ├── requirements.txt    # Python 依赖
│   └── 客户联络看板.html    # 离线备用版（内嵌完整数据）
```

## 数据更新流程

1. 将最新的 `销售明细.xlsx` 和 `客户联络.xlsx` 放入 `contact/` 文件夹
2. 运行 `python build_dashboard.py`
3. 所有用户刷新页面即可看到最新数据

如需跳过 Supabase 上传（仅更新本地离线版）：
```bash
python build_dashboard.py --no-upload
```

## 依赖

- Python 3.8+
- Flask, waitress, openpyxl, pandas, numpy
- Supabase 账号（免费层足够）
