"""
客户联络看板 - 共享服务器
启动后同一局域网内的同事均可通过浏览器访问和修改数据。
Usage: python server.py
       python server.py --port 8080
       python server.py --host 0.0.0.0 --port 80
"""
import sys
import os
import json
import threading
import time
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_file
except ImportError:
    print("需要安装 Flask: python -m pip install flask")
    sys.exit(1)

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
HTML_FILE = BASE_DIR / '客户联络看板.html'
STATE_FILE = BASE_DIR / 'shared_state.json'
LOCK = threading.Lock()

# ---------- state management ----------
def load_state():
    """读取共享状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'checked': {}, 'reasons': {}, 'updatedBy': '', 'updatedAt': ''}

def save_state(state):
    """保存共享状态（带文件锁）"""
    with LOCK:
        tmp = str(STATE_FILE) + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATE_FILE)  # atomic on Windows

# ---------- routes ----------
@app.route('/')
def index():
    """返回看板 HTML"""
    return send_file(str(HTML_FILE))

@app.route('/api/state', methods=['GET'])
def get_state():
    """获取共享状态"""
    state = load_state()
    return jsonify(state)

@app.route('/api/state', methods=['POST'])
def update_state():
    """更新共享状态"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': '无效数据'}), 400

    state = load_state()

    # 合并勾选状态
    if 'checked' in data:
        for name, val in data['checked'].items():
            if val:
                state['checked'][name] = True
            else:
                state['checked'].pop(name, None)

    # 合并原因
    if 'reasons' in data:
        for name, reason in data['reasons'].items():
            if reason:
                state['reasons'][name] = reason
            else:
                state['reasons'].pop(name, None)

    # 批量替换勾选（全选/取消时发完整列表）
    if 'checkedReplace' in data:
        state['checked'] = data['checkedReplace']

    # 批量替换原因
    if 'reasonsReplace' in data:
        state['reasons'] = data['reasonsReplace']

    state['updatedBy'] = data.get('updatedBy', '')
    state['updatedAt'] = time.strftime('%Y-%m-%d %H:%M:%S')

    save_state(state)
    return jsonify({'ok': True, 'updatedAt': state['updatedAt']})

# ---------- main ----------
def print_startup_info(host, port):
    lan_ip = get_lan_ip()
    lines = [
        '',
        '=' * 56,
        '  Customer Contact Dashboard - Server Started',
        '=' * 56,
        '',
        '  Local access:',
        f'    http://127.0.0.1:{port}',
        f'    http://localhost:{port}',
        '',
    ]
    if lan_ip:
        lines += [
            '  LAN access (colleagues use this):',
            f'    http://{lan_ip}:{port}',
            '',
        ]
    lines += [
        '  Press Ctrl+C to stop',
        '=' * 56,
        '',
    ]
    for line in lines:
        print(line)

def get_lan_ip():
    """获取局域网 IP"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Customer Contact Dashboard Server')
    parser.add_argument('--host', default='0.0.0.0', help='Listen address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None, help='Port (default: 5000 or $PORT)')
    parser.add_argument('--prod', action='store_true', help='Use production WSGI server (waitress)')
    args = parser.parse_args()

    # Use PORT env var if set (for cloud deployment), otherwise use arg or default 5000
    port = args.port or int(os.environ.get('PORT', 5000))

    # Ensure HTML exists
    if not HTML_FILE.exists():
        print(f'ERROR: Cannot find {HTML_FILE}')
        sys.exit(1)

    print_startup_info(args.host, port)

    if args.prod or os.environ.get('PRODUCTION'):
        try:
            from waitress import serve
            print('  [Production mode] Using waitress WSGI server')
            serve(app, host=args.host, port=port)
        except ImportError:
            print('  waitress not installed, falling back to Flask dev server')
            app.run(host=args.host, port=port, debug=False)
    else:
        app.run(host=args.host, port=port, debug=False)
