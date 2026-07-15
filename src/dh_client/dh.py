"""数字家园 CLI 客户端。

通过守护进程 HTTP API 发送命令。
需要先启动守护进程: python -m dh_client.daemon

用法:
    python -m dh_client.dh <命令>
    python -m dh_client.dh look
    python -m dh_client.dh "get 石头"
"""

import json
import sys
import urllib.error
import urllib.request

# Windows 下强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_API_URL = "http://localhost:5000"


def main():
    action = " ".join(sys.argv[1:])
    if not action:
        print("用法: python -m dh_client.dh <命令>")
        print("示例: python -m dh_client.dh look")
        sys.exit(1)

    try:
        req = urllib.request.Request(
            f"{_API_URL}/action",
            data=json.dumps({"action": action}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if result.get("ok"):
            # 先打印未读消息（椰子掉落、被攻击、别人说话……）
            unread = result.get("unread", [])
            if unread:
                for msg in unread:
                    print(f"[未读] {msg}")
                print("---")
            print(result["response"])
        else:
            print(f"错误：{result.get('error', '未知错误')}")

    except urllib.error.URLError:
        print("守护进程未运行，请先启动: python -m dh_client.daemon")
    except Exception as e:
        print(f"通信异常：{e}")


if __name__ == "__main__":
    main()
