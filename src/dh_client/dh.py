"""数字家园 CLI 客户端。

用法:
    python -m dh_client.dh <命令>
    python -m dh_client.dh look
    python -m dh_client.dh "get 石头"
"""

import asyncio
import sys
import os

# Windows 下强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from .config import load_config
from .connector import send_action


def main():
    action = " ".join(sys.argv[1:])
    if not action:
        print("用法: python -m dh_client.dh <命令>")
        print("示例: python -m dh_client.dh look")
        sys.exit(1)

    config = load_config()
    result = asyncio.run(send_action(config, action))
    print(result)


if __name__ == "__main__":
    main()
