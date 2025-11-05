#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试服务器客户端 - 快速调用API
示例：
  python test_client.py status          # 查看状态
  python test_client.py reset           # 重置首页
  python test_client.py city 北京       # 切换城市
  python test_client.py search 鹭卓     # 搜索
  python test_client.py click 鹭卓      # 点击演出
  python test_client.py screenshot      # 截图
"""
import sys
import requests
import json

BASE_URL = "http://localhost:8000"

def call_api(endpoint, params=None):
    """调用API"""
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=30)
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    except requests.exceptions.ConnectionError:
        print("[ERROR] 无法连接到服务器，请确保服务器正在运行：python test_server.py")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "status":
        call_api("status")

    elif command == "reset":
        call_api("reset")

    elif command == "city":
        if len(sys.argv) < 3:
            print("用法: python test_client.py city <城市名>")
            sys.exit(1)
        city = sys.argv[2]
        call_api("city", {"city": city})

    elif command == "search":
        if len(sys.argv) < 3:
            print("用法: python test_client.py search <关键词>")
            sys.exit(1)
        keyword = " ".join(sys.argv[2:])
        call_api("search", {"keyword": keyword})

    elif command == "click":
        if len(sys.argv) < 3:
            # 点击第一个
            call_api("click", {"index": 0})
        else:
            keyword = " ".join(sys.argv[2:])
            call_api("click", {"keyword": keyword})

    elif command == "screenshot":
        filename = sys.argv[2] if len(sys.argv) > 2 else "api_screenshot.png"
        call_api("screenshot", {"filename": filename})

    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
