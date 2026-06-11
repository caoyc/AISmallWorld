"""
部署脚本步骤 6：创建 AI 玩家账号和角色

通过一条 @py 命令完成：创建账号 + 创建角色 + 放置到白色沙滩。
"""
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import telnetlib  # noqa: E402

tn = telnetlib.Telnet('127.0.0.1', 4000, timeout=10)
time.sleep(1)
tn.read_very_eager()

tn.write('connect mofi Mofi#2026Island\n'.encode('utf-8'))
time.sleep(2)
tn.read_very_eager()

# 用 Evennia 自带的 create_account 创建账号（密码哈希兼容）
cmd = (
    "@py "
    "from evennia.utils.create import create_account, create_object; "
    "from evennia.objects.models import ObjectDB; "
    "from survival.characters import SurvivalCharacterV2; "
    "spawn_room = ObjectDB.objects.get(id=10); "
    "acc = create_account('yueying', 'gzdmcaoyc@163.com', 'Yueying#2026Island'); "
    "ch = create_object(SurvivalCharacterV2, key='yueying', home=spawn_room); "
    "ch.move_to(spawn_room, quiet=True); "
    "chars = acc.db._playable_characters or []; "
    "chars.append(ch); "
    "acc.db._playable_characters = chars; "
    "ch.locks.add('puppet:id(%s) or pid(%s) or perm(Developer)' % (ch.id, acc.id)); "
    "print('ALL OK acc=%s char=%s' % (acc.dbref, ch.dbref))"
)
tn.write((cmd + '\n').encode('utf-8'))
time.sleep(5)
resp = tn.read_very_eager().decode('utf-8', errors='replace')
print('RESULT:', resp)

if 'ALL OK' in resp:
    print("CREATE OK")
    print("CHAR OK")
else:
    print("FAILED")
    tn.write('quit\n'.encode('utf-8'))
    tn.close()
    sys.exit(1)

tn.write('quit\n'.encode('utf-8'))
time.sleep(1)
tn.close()
