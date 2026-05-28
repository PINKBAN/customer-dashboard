"""
客户联络看板 - 静态文件服务器
仅负责提供 HTML 文件访问，所有数据同步通过 Supabase 完成。

Usage: python server.py
       python server.py --port 8080
       python server.py --prod
"""
import sys
import os
from pathlib import Path

try:
    from flask import Flask, send_file
except ImportError:
    print("需要安装 Flask: pip install flask")
    sys.exit(1)

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
HTML_FILE = BASE_DIR / '客户联络看板.html'
INDEX_FILE = ROOT_DIR / 'index.html'
CONFIG_FILE = ROOT_DIR / 'config.js'


@app.route('/')
def index():
    return send_file(str(INDEX_FILE))


@app.route('/config.js')
def config_js():
    return send_file(str(CONFIG_FILE))


@app.route('/<path:filename>')
def static_files(filename):
    # 先尝试 contact 目录，再尝试根目录
    contact_path = BASE_DIR / filename
    if contact_path.exists():
        return send_file(str(contact_path))
    root_path = ROOT_DIR / filename
    if root_path.exists():
        return send_file(str(root_path))
    return 'Not Found', 404


def print_startup_info(host, port):
    lan_ip = _get_lan_ip()
    lines = [
        '',
        '=' * 56,
        '  客户联络看板 - 服务器已启动',
        '=' * 56,
        '',
        '  本地访问:',
        f'    http://127.0.0.1:{port}',
        f'    http://localhost:{port}',
    ]
    if lan_ip:
        lines += [
            '',
            '  局域网访问:',
            f'    http://{lan_ip}:{port}',
        ]
    lines += [
        '',
        '  所有数据通过 Supabase 实时同步',
        '  Press Ctrl+C to stop',
        '=' * 56,
        '',
    ]
    for line in lines:
        print(line)


def _get_lan_ip():
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
    parser = argparse.ArgumentParser(description='客户联络看板 - 静态服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None, help='端口 (默认: 5000 或 $PORT)')
    parser.add_argument('--prod', action='store_true', help='使用 waitress 生产服务器')
    args = parser.parse_args()

    port = args.port or int(os.environ.get('PORT', 5000))

    print_startup_info(args.host, port)

    if args.prod or os.environ.get('PRODUCTION'):
        try:
            from waitress import serve
            print('  [生产模式] 使用 waitress WSGI 服务器')
            serve(app, host=args.host, port=port)
        except ImportError:
            print('  waitress 未安装，使用 Flask 开发服务器')
            app.run(host=args.host, port=port, debug=False)
    else:
        app.run(host=args.host, port=port, debug=False)
