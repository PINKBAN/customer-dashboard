#!/bin/bash
# 客户联络看板 - 启动服务器 (Mac/Linux)
cd "$(dirname "$0")/contact"
python3 server.py --prod
