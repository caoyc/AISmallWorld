"""
部署脚本步骤 5：构建荒岛世界

通过 telnet 连接 Evennia，执行 @py 构建命令。
"""
import sys
import os
import time

# 确保终端 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

# 确保 src 在搜索路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import telnetlib  # noqa: E402

tn = telnetlib.Telnet('127.0.0.1', 4000, timeout=10)
time.sleep(1)
tn.read_very_eager()

tn.write('connect mofi Mofi#2026Island\n'.encode('utf-8'))
time.sleep(2)
tn.read_very_eager()

tn.write('@py from survival.world.build_island import build; build()\n'.encode('utf-8'))
time.sleep(10)
resp = tn.read_very_eager().decode('utf-8', errors='replace')
print('BUILD:', resp[:500])

tn.write(
    "@py from evennia.objects.models import ObjectDB; "
    "r=ObjectDB.objects.filter(db_key='白色沙滩'); "
    "print(r.first().dbref if r.exists() else 'NOT FOUND')\n"
    .encode('utf-8')
)
time.sleep(3)
resp = tn.read_very_eager().decode('utf-8', errors='replace')
print('BEACH:', resp)

tn.write('quit\n'.encode('utf-8'))
time.sleep(1)
tn.close()
