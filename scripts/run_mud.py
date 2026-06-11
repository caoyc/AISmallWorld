"""无限制运行 MUD 客户端，直到手动终止。"""
import asyncio
import logging
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

log_file = os.path.join(os.path.dirname(__file__), "..", "logs", "game.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])

from mud_client.main import load_config, run

logging.getLogger("game").info("=== MUD 客户端启动（无时间限制） ===")
asyncio.run(run())
logging.getLogger("game").info("=== MUD 客户端关闭 ===")
