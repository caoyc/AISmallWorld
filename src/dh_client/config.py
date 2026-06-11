"""配置加载模块。

从 dh_config.json 读取 Evennia 连接配置。
"""

import json
import os
import sys
from dataclasses import dataclass


@dataclass
class Config:
    """Evennia 连接配置。"""

    evennia_host: str = "localhost"
    evennia_port: int = 4002
    account: str = ""
    password: str = ""


def load_config(config_path: str = "") -> Config:
    """加载配置文件。默认在项目根目录查找 dh_config.json。"""
    if not config_path:
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        config_path = os.path.join(root, "dh_config.json")

    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    evennia = raw.get("evennia", {})
    config = Config(
        evennia_host=evennia.get("host", "localhost"),
        evennia_port=evennia.get("port", 4002),
        account=evennia.get("account", ""),
        password=evennia.get("password", ""),
    )

    if not config.account or not config.password:
        print("配置缺少账号(account)或密码(password)")
        sys.exit(1)

    return config
