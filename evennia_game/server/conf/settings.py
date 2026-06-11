r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "evennia_game"

######################################################################
# Python path - 添加 src 目录
######################################################################

import os
import sys

_sys_path = os.path.normpath(os.path.join(GAME_DIR, os.pardir, "src"))
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

######################################################################
# 默认 Typeclass 配置
######################################################################

BASE_CHARACTER_TYPECLASS = "survival.v2.characters.SurvivalCharacterV2"
BASE_ROOM_TYPECLASS = "survival.v2.rooms.SurvivalRoomV2"

# v2 prototype 注册
PROTOTYPE_MODULES = ["survival.v2.prototypes"]

# 自定义锁函数
LOCK_FUNC_MODULES = (
    "evennia.locks.lockfuncs",
    "survival.v2.utils.lockfuncs",
)

# 出生点（build 前注释，build 后恢复）
DEFAULT_HOME = "#10"
START_LOCATION = "#10"


######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
