"""
v2 世界构建脚本

构建荒岛世界：18 个房间、28 条出口、23+ 个对象。
沿用 v1 的 ROOM_DATA 和 EXIT_DATA，对象层用 spawn() 替代 create_object()。

基础生存闭环新增：资源来源、配方等对象，分配到已有房间。
暂不新增房间（地图扩展待后续任务），新对象放到合理的现有房间中。

使用方式：
    @py from survival.v2.world.build_island import build; build()

详见：docs/设计文档/解决饥渴_v2/详细设计/世界构建.md
详见：docs/设计文档/石刃业务闭环/详细设计/世界构建.md
详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v1/基础生存闭环详细设计.md
详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v6/LC-03a/LC-03a详细设计.md
"""

from evennia.objects.objects import DefaultExit
from evennia.prototypes.spawner import spawn
from evennia.utils.create import create_object

from survival.v1.build_island import EXIT_DATA, ROOM_DATA
from survival.v2.rooms import SurvivalRoomV2

# 使用自定义 Exit（覆写 at_traverse 打断休息状态）替代 DefaultExit
from typeclasses.exits import Exit as SurvivalExit

# v2 对象数据：(prototype_key, key覆盖或None, 所在房间名)
#
# 房间分配策略（待新地图扩展后调整）：
#   - 资源来源对象放到主题匹配的已有房间
#   - 配方暂放在古树广场（玩家可到达的初始位置）
#   - 标注 [临时] 的分配在地图扩展后需迁移
OBJECT_DATA = [
    # ---- v2 解决饥渴 水源/食物 ----
    # 淡水水源（mountain_lake_water 兼具 resource + fish_resource，替代 fresh_water）
    ("mountain_lake_water", None, "山地湖泊"),
    ("mountain_lake_water", "溪流水潭", "溪流水潭"),
    ("fresh_water", "溪流", "溪流上游"),
    ("murky_stream", None, "溪流中游"),
    # 咸水水源
    ("salt_water", "大海", "白色沙滩"),
    ("salt_water", "大海", "海滩东段"),
    ("salt_water", "大海", "海滩西段"),
    ("salt_water", "大海", "海滩北段"),
    # 食物资源 — 椰子树（按房间描述密度分布：稀疏→浓密）
    ("coconut_tree", None, "椰林边缘"),
    ("coconut_tree", None, "椰林边缘"),
    ("coconut_tree", None, "椰林深处"),
    ("coconut_tree", None, "椰林深处"),
    ("coconut_tree", None, "椰林深处"),
    ("coconut_tree", None, "椰林深处"),
    ("coconut_tree", None, "沿海灌木带"),
    ("berry_bush", None, "浆果丛"),
    ("shellfish", None, "礁石滩"),

    # ---- 石刃闭环新增 ----
    # 碎石堆（资源来源）
    ("rubble", None, "碎石坡"),
    # 藤本植物 ×3（丛林入口）
    ("vine_plant_1", "鞭藤", "丛林入口"),
    ("vine_plant_2", "白藤", "丛林入口"),
    ("vine_plant_3", "葛藤", "丛林入口"),
    # 藤本植物 ×2（溪流中游）
    ("vine_plant_4", "过江龙", "溪流中游"),
    ("vine_plant_5", "毛茉栾藤", "溪流中游"),
    # 宿主大树 ×3（丛林深处）+ 藤蔓植物 ×1
    ("host_tree_1", "环纹榕", "丛林深处"),
    ("host_tree_2", "榄仁树", "丛林深处"),
    ("host_tree_3", "红厚壳", "丛林深处"),
    ("vine_plant_1", "鞭藤", "丛林深处"),
    # 宿主大树 ×2（古树广场）
    ("host_tree_4", "滨玉蕊", "古树广场"),
    ("host_tree_5", "太平洋栗", "古树广场"),
    # 配方放置（古树广场保留石刃配方作为初始引导）
    ("recipe_stone_blade", None, "古树广场"),

    # ---- 基础生存闭环新增 ----
    # 资源来源（椰林边缘稀疏→深处密集）
    ("palm_sapling", None, "椰林边缘"),
    ("palm_sapling", None, "椰林边缘"),
    ("palm_sapling", None, "椰林深处"),

    # ---- v7 资源迁移（LC-03a/LC-03b/LC-04/LC-05 联合）----
    # 竹林
    ("bamboo", None, "竹林"),
    ("bamboo", None, "竹林"),
    ("bamboo", None, "竹林"),
    # 芭蕉林（热带果林群落）
    ("banana_tree", None, "芭蕉林"),
    ("banana_tree", None, "芭蕉林"),
    ("banana_plant", None, "芭蕉林"),
    ("banana_plant", None, "芭蕉林"),
    ("travelers_palm", None, "芭蕉林"),
    # 苔藓幽谷
    ("moss_plant", None, "苔藓幽谷"),
    ("moss_plant", None, "苔藓幽谷"),
    ("moss_plant", None, "苔藓幽谷"),
    ("moss_plant", None, "苔藓幽谷"),
    ("weed", None, "苔藓幽谷"),
    ("weed", None, "苔藓幽谷"),
    # 火山岩脊
    ("moss_plant", None, "火山岩脊"),
    ("moss_plant", None, "火山岩脊"),
    # 开阔草地
    ("weed", None, "开阔草地"),
    ("weed", None, "开阔草地"),
    ("weed", None, "开阔草地"),
    ("weed", None, "开阔草地"),
    ("palm_sapling", None, "开阔草地"),
    # 瀑布崖
    ("vine_plant_1", "鞭藤", "瀑布崖"),
    ("vine_plant_3", "葛藤", "瀑布崖"),
    # 巨榕根部
    ("host_tree_1", "环纹榕", "巨榕根部"),
    ("host_tree_2", "榄仁树", "巨榕根部"),
    ("vine_plant_2", "白藤", "巨榕根部"),
    ("vine_plant_5", "毛茉栾藤", "巨榕根部"),
    # 溪流分支
    ("vine_plant_4", "过江龙", "溪流分支"),
    ("weed", None, "溪流分支"),
    # 热带花卉坡
    ("weed", None, "热带花卉坡"),
    ("travelers_palm", None, "热带花卉坡"),
    # 沿海灌木带
    ("palm_sapling", None, "沿海灌木带"),
    ("palm_sapling", None, "沿海灌木带"),
    ("weed", None, "沿海灌木带"),
    # 榕树（旧名 mature_big_tree/young_big_tree/small_tree 已替换）
    ("ficus_sapling", None, "丛林入口"),    # 原 small_tree 位置
    ("travelers_palm", None, "丛林入口"),
    # 密林小径榕树（从丛林深处迁入+增量）
    ("ficus_tree", None, "密林小径"),
    ("ficus_tree", None, "密林小径"),
    ("ficus_young", None, "密林小径"),
    # 海蚀洞深处水潭（从海蚀洞口迁入）
    ("cave_pool", None, "海蚀洞深处"),
    # 红树林深处水域（新增）
    ("mangrove_water", None, "红树林深处"),

    # ---- LC-04 捕鱼闭环新增 ----
    # 水域对象（按生态原则复用已有 prototype，key + desc 贴合当地环境）
    ("mangrove_water", None, "红树林浅滩"),
    # 淡水溪潭（复用 mountain_lake_water：热带淡水生态，兼具饮水+捕鱼）
    ("mountain_lake_water", "深潭", "深潭", [
        ("desc_look", "墨绿色的深潭水面平静无波，偶尔有鱼跃出激起涟漪。"),
    ]),
    # 红树林湿地延伸（复用 mangrove_water：半咸水生态）
    ("mangrove_water", "泥滩水洼", "潮间泥滩", [
        ("desc_look", "泥滩间散布着大小不一的水洼，退潮后困住的浑浊海水在阳光下泛着微光。"),
    ]),
    # 珊瑚礁潟湖（复用 cave_pool：热带海水生态）
    ("cave_pool", "潟湖海水", "珊瑚潟湖", [
        ("desc_look", "碧绿的潟湖海水清澈见底，五彩斑斓的珊瑚丛间游弋着热带鱼群。"),
    ]),
    ("cave_pool", "浅滩海水", "潟湖浅滩", [
        ("desc_look", "温热的浅滩海水只到脚踝，细白的珊瑚沙底清晰可见，小鱼群在海草间穿梭。"),
    ]),

    # 其余配方通过 research 获得，不在地面放置
]


def build():
    """构建荒岛世界（v2 prototype 驱动版）。

    流程：
        mermaid:
        TD
            A[build] --> B[create_rooms]
            B --> C[create_exits]
            C --> D[spawn_objects]
            D --> E[返回 rooms 和 spawn_room]

    Returns:
        dict: 包含 rooms（房间字典）和 spawn_room（出生点）。
    """
    rooms = create_rooms()
    create_exits(rooms)
    spawn_objects(rooms)

    spawn_room = rooms.get("白色沙滩")
    return {"rooms": rooms, "spawn_room": spawn_room}


def create_rooms():
    """创建 17 个房间，设置五感描述。

    Returns:
        dict: {房间名: room对象}
    """
    rooms = {}
    for room_key, (resource_type, desc_look, desc_listen, desc_smell, desc_touch, desc_taste) in ROOM_DATA.items():
        room = create_object(SurvivalRoomV2, key=room_key, nohome=True)
        room.home = room  # 房间 home 指向自身，不依赖 DEFAULT_HOME
        room.db.desc = desc_look
        room.db.desc_look = desc_look
        room.db.desc_listen = desc_listen
        room.db.desc_smell = desc_smell
        room.db.desc_touch = desc_touch
        room.db.desc_taste = desc_taste
        rooms[room_key] = room

    # ── LC-03a §7.15 修改 1：森林房间资源迁移 ──
    # 将 forest_grove 对象的 resource 迁移到房间
    jungle_room = rooms.get("丛林深处")
    if jungle_room:
        jungle_room.key = "热带丛林"
        jungle_room.db.resource = [
            {"prototype": "wood_stick", "chance": 0.5, "method": "search",
             "success_desc": "落叶堆下露出一截淡黄色的木质，一根木棍半埋在腐叶里。", "fail_desc": ""},
            {"prototype": "tree_branch", "chance": 0.6, "method": "search",
             "success_desc": "脚边的枯枝踩上去嘎吱作响，有一根手指粗细的断枝夹在树根间。", "fail_desc": ""},
            {"prototype": "long_stick", "chance": 0.1, "method": "search",
             "success_desc": "灌木丛后斜靠着一根一人高的直木棍，表面被风雨磨得发白。", "fail_desc": ""},
            {"prototype": "log", "chance": 0.1, "method": "search",
             "success_desc": "两棵树的根部横着一截粗壮的原木，上面已经长了一层薄薄的苔藓。", "fail_desc": ""},
        ]

    # ── LC-03a §7.15 修改 2：椰树房间 resource ──
    coconut_room = rooms.get("椰林深处")
    if coconut_room:
        coconut_room.db.resource = [
            {"prototype": "coconut", "chance": 0.1, "method": "search",
             "success_desc": "枯叶堆里滚出一个青绿的椰子，外壳还沾着泥土。", "fail_desc": ""},
            {"prototype": "coconut_shell", "chance": 0.1, "method": "search",
             "success_desc": "枯叶下露出一块白色的弧面——一个切开的椰壳，切口平整。", "fail_desc": ""},
            {"prototype": "palm_leaf", "chance": 0.15, "method": "search",
             "success_desc": "几片棕榈叶从树冠落下还叠在一起，没有完全干枯。", "fail_desc": ""},
        ]

    # ── v7 密林小径房间级 resource ──
    dense_forest_room = rooms.get("密林小径")
    if dense_forest_room:
        dense_forest_room.db.resource = [
            {"prototype": "wood_stick", "chance": 0.5, "method": "search",
             "success_desc": "落叶层下踩到一根硬挺的东西，扒开一看是根木棍。", "fail_desc": ""},
            {"prototype": "tree_branch", "chance": 0.6, "method": "search",
             "success_desc": "脚边的枯枝踩上去嘎吱作响，有一根还算完整的断枝。", "fail_desc": ""},
            {"prototype": "long_stick", "chance": 0.1, "method": "search",
             "success_desc": "靠着树根斜插着一根长木棍，已经脱了皮，表面灰白光滑。", "fail_desc": ""},
            {"prototype": "log", "chance": 0.1, "method": "search",
             "success_desc": "苔藓下面隐约露出一段粗壮的原木截面，年轮清晰可见。", "fail_desc": ""},
        ]

    # ── v7 房间描述由 ROOM_DATA（v1/build_island.py）统一提供 ──
    # ROOM_DATA 中的描述已按设计文档（房间描述重写.md）的生态梯度规划编写，
    # 此处不再覆写，保持生态一致性。

    return rooms


def create_exits(rooms):
    """创建 28 条双向出口。

    Args:
        rooms (dict): {房间名: room对象}
    """
    for source_key, dest_key, exit_key in EXIT_DATA:
        source_room = rooms[source_key]
        dest_room = rooms[dest_key]
        parts = exit_key.split(";")
        key = parts[0]
        aliases = parts[1:] if len(parts) > 1 else []
        create_object(
            SurvivalExit,
            key=key,
            aliases=aliases,
            location=source_room,
            destination=dest_room,
        )


def spawn_objects(rooms):
    """spawn 所有资源对象。

    使用 Evennia 原生的 dict prototype 机制覆盖 key：
    传 dict 给 spawn()，通过 prototype_parent 继承已有 prototype，
    同时覆盖 key 和其他属性。这是 Evennia 设计的标准用法。

    OBJECT_DATA 条目格式：
        (prototype_key, key_override或None, room_name)
        (prototype_key, key_override或None, room_name, {attrs覆写})

    Args:
        rooms (dict): {房间名: room对象}
    """
    from survival.v2.scripts.coconut_drop import attach_coconut_drop_timer

    for entry in OBJECT_DATA:
        prototype_key = entry[0]
        key_override = entry[1]
        room_name = entry[2]
        attrs_override = entry[3] if len(entry) > 3 else None

        if key_override or attrs_override:
            prototype = {"prototype_parent": prototype_key}
            if key_override:
                prototype["key"] = key_override
            if attrs_override:
                prototype["attrs"] = attrs_override
        else:
            prototype = prototype_key
        objs = spawn(prototype)
        if objs:
            obj = objs[0]
            room = rooms.get(room_name)
            if room:
                obj.move_to(room, quiet=True)
            # 椰子树：spawn 后手动挂载掉落计时器
            if prototype_key == "coconut_tree":
                attach_coconut_drop_timer(obj)
