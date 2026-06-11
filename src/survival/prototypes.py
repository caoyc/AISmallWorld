"""
v2 prototype 注册表

所有 prototype 定义在此模块，通过 settings.py 的 PROTOTYPE_MODULES 加载。
顺序：父级必须在子级之前，因为 prototype_parent 必须引用已注册的 prototype。

详见：docs/设计文档/解决饥渴_v2/详细设计/prototype注册.md
"""

PROTOTYPE_LIST = [
    # ── 顶层基类 ──
    {
        "prototype_key": "non_living",
        "typeclass": "survival.objects.NonLiving",
        "key": "非生物",
    },
    {
        "prototype_key": "organism",
        "typeclass": "survival.objects.Organism",
        "key": "生物",
    },

    # ── 燃烧残留物分类链 ──
    {
        "prototype_key": "combustion_residue",
        "prototype_parent": "non_living",
        "key": "燃烧残留物",
        "attrs": [
            ("item_type", "solid"),
        ],
    },
    {
        "prototype_key": "wood_ash",
        "prototype_parent": "combustion_residue",
        "key": "草木灰",
        "attrs": [
            ("desc_look", "一把灰白色的细粉，带着木柴烧尽后的干燥气息，质地轻柔，很容易被风吹散。"),
            ("desc_smell", "草木灰散发着淡淡的碱性气味，混着烧焦木头的余味。"),
        ],
    },

    # ── GB/T 7635 分类链：淡水（编码 18）──
    {
        "prototype_key": "gb_18",
        "prototype_parent": "non_living",
        "key": "水",
    },
    {
        "prototype_key": "gb_180",
        "prototype_parent": "gb_18",
        "key": "自然水",
    },
    {
        "prototype_key": "gb_1802",
        "prototype_parent": "gb_180",
        "key": "地表水",
    },

    # ── GB/T 7635 分类链：海水（编码 162）──
    {
        "prototype_key": "gb_162",
        "prototype_parent": "non_living",
        "key": "盐和海水",
    },
    {
        "prototype_key": "gb_1622",
        "prototype_parent": "gb_162",
        "key": "海水",
    },

    # ── COL 分类链：Plantae（植物界）──
    {
        "prototype_key": "plantae",
        "prototype_parent": "organism",
        "key": "植物界",
    },
    {
        "prototype_key": "plantae_tracheophyta",
        "prototype_parent": "plantae",
        "key": "维管植物门",
    },
    # 椰子树路径
    {
        "prototype_key": "plantae_liliopsida",
        "prototype_parent": "plantae_tracheophyta",
        "key": "百合纲",
    },
    {
        "prototype_key": "plantae_arecales",
        "prototype_parent": "plantae_liliopsida",
        "key": "棕榈目",
    },
    {
        "prototype_key": "plantae_arecaceae",
        "prototype_parent": "plantae_arecales",
        "key": "棕榈科",
    },
    {
        "prototype_key": "plantae_arecaceae_cocos",
        "prototype_parent": "plantae_arecaceae",
        "key": "椰属",
    },
    {
        "prototype_key": "plantae_arecaceae_cocos_nucifera",
        "prototype_parent": "plantae_arecaceae_cocos",
        "key": "椰子",
    },
    # 浆果灌木路径
    {
        "prototype_key": "plantae_magnoliopsida",
        "prototype_parent": "plantae_tracheophyta",
        "key": "木兰纲",
    },
    {
        "prototype_key": "plantae_rosales",
        "prototype_parent": "plantae_magnoliopsida",
        "key": "蔷薇目",
    },
    {
        "prototype_key": "plantae_rosaceae",
        "prototype_parent": "plantae_rosales",
        "key": "蔷薇科",
    },
    {
        "prototype_key": "plantae_rosaceae_rubus",
        "prototype_parent": "plantae_rosaceae",
        "key": "悬钩子属",
    },

    # ── COL 分类链：Animalia（动物界）──
    {
        "prototype_key": "animalia",
        "prototype_parent": "organism",
        "key": "动物界",
    },
    {
        "prototype_key": "animalia_mollusca",
        "prototype_parent": "animalia",
        "key": "软体动物门",
    },
    {
        "prototype_key": "animalia_mollusca_bivalvia",
        "prototype_parent": "animalia_mollusca",
        "key": "双壳纲",
    },

    # ── COL 动物分类链扩展（LC-04） ──
    {
        "prototype_key": "animalia_chordata",
        "prototype_parent": "animalia",
        "key": "脊索动物门",
    },
    {
        "prototype_key": "animalia_actinopterygii",
        "prototype_parent": "animalia_chordata",
        "key": "辐鳍鱼纲",
    },
    {
        "prototype_key": "animalia_arthropoda",
        "prototype_parent": "animalia",
        "key": "节肢动物门",
    },
    {
        "prototype_key": "animalia_malacostraca",
        "prototype_parent": "animalia_arthropoda",
        "key": "软甲纲",
    },
    {
        "prototype_key": "animalia_decapoda",
        "prototype_parent": "animalia_malacostraca",
        "key": "十足目",
    },
    {
        "prototype_key": "animalia_brachyura",
        "prototype_parent": "animalia_decapoda",
        "key": "短尾下目",
    },
    {
        "prototype_key": "animalia_mollusca_gastropoda",
        "prototype_parent": "animalia_mollusca",
        "key": "腹足纲",
    },

    # ── 部件类型（无属性，纯分类标记）──
    {
        "prototype_key": "plantpart",
        "prototype_parent": "organism",
        "key": "植物部件",
    },
    {
        "prototype_key": "plantpart_fruit",
        "prototype_parent": "plantpart",
        "key": "果实",
    },
    {
        "prototype_key": "animalpart",
        "prototype_parent": "organism",
        "key": "动物部件",
    },
    {
        "prototype_key": "animalpart_meat",
        "prototype_parent": "animalpart",
        "key": "肉类",
    },

    # ── 资源来源 prototype（不可拾取）──
    {
        "prototype_key": "fresh_water",
        "prototype_parent": "gb_1802",
        "key": "淡水",
        "locks": "get:false()",
        "attrs": [
            ("resource", [{"prototype": "fresh_water_item", "chance": 1.0}]),
            ("desc_look", "清澈的水面泛着粼粼波光。"),
            ("desc_smell", "清新的水汽扑面而来。"),
            ("desc_taste", "清甜，没有异味。"),
        ],
    },
    {
        "prototype_key": "salt_water",
        "prototype_parent": "gb_1622",
        "key": "大海",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "salt_water_item", "chance": 0.5},
                {"prototype": "wood_stick", "chance": 0.05, "method": "search",
                 "success_desc": "海浪推上来一根被盐水泡得发白的木棍。", "fail_desc": ""},
                {"prototype": "long_stick", "chance": 0.05, "method": "search",
                 "success_desc": "一根长长的漂流木搁浅在沙滩上，表面被海水磨得光滑。", "fail_desc": ""},
                {"prototype": "tree_branch", "chance": 0.05, "method": "search",
                 "success_desc": "浪花退去，露出一截断裂的树枝，上面还挂着干枯的海草。", "fail_desc": ""},
                {"prototype": "coconut", "chance": 0.05, "method": "search",
                 "success_desc": "一个椰子随着海浪漂到了岸边，外壳湿漉漉的。", "fail_desc": ""},
                {"prototype": "palm_leaf", "chance": 0.05, "method": "search",
                 "success_desc": "一片棕榈叶被海浪冲上了沙滩，叶缘已经被盐水浸得发黄。", "fail_desc": ""},
                {"prototype": "fresh_grass", "chance": 0.05, "method": "search",
                 "success_desc": "一团墨绿色的海草缠在礁石上，叶片肥厚，散发着咸腥的海水气息。", "fail_desc": ""},
            ]),
            ("desc_look", "碧蓝的大海一望无际，波浪轻轻拍打着岸边。"),
            ("desc_smell", "咸湿的海风带着腥味。"),
            ("desc_taste", "咸涩苦腥。"),
        ],
    },
    {
        "prototype_key": "coconut_tree",
        "prototype_parent": "plantae_arecaceae_cocos_nucifera",
        "typeclass": "survival.objects.CoconutTree",
        "key": "椰子树",
        "locks": "get:false()",
        "attrs": [
            ("resource", [{"prototype": "coconut", "chance": 0.4}]),
            ("desc_look", "高大的椰子树笔直矗立，树冠间隐约可见椰子的轮廓。"),
            ("desc_smell", "椰树的清香混合着泥土的气息。"),
        ],
    },
    {
        "prototype_key": "berry_bush",
        "prototype_parent": "plantae_rosaceae_rubus",
        "key": "浆果灌木",
        "locks": "get:false()",
        "attrs": [
            ("resource", [{"prototype": "berry", "chance": 0.5}]),
            ("desc_look", "一丛低矮的灌木，枝叶间隐约可见红色的浆果。"),
            ("desc_smell", "空气中弥漫着浆果的甜香。"),
        ],
    },
    {
        "prototype_key": "shellfish",
        "prototype_parent": "animalia_mollusca_bivalvia",
        "key": "礁石缝隙",
        "locks": "get:false()",
        "attrs": [
            ("resource", [{"prototype": "shellfish_item", "chance": 0.3}]),
            ("desc_look", "礁石缝隙间偶尔能看到贝壳的痕迹。"),
            ("desc_smell", "咸湿的礁石散发着海腥味。"),
        ],
    },

    # ── 食物物品 prototype（可拾取，无锁）──
    {
        "prototype_key": "coconut",
        "prototype_parent": ("plantae_arecaceae_cocos_nucifera", "plantpart_fruit"),
        "key": "椰子",
        "attrs": [
            ("cut_into", "cut_coconut"),
            ("defense", 1),
            ("hp", 2),
            ("hunger_restore", 20),
            ("thirst_restore", 20),
            ("desc_look", "一个青绿色的椰子，外壳坚硬粗糙。"),
            ("desc_smell", "淡淡的植物清香。"),
            ("desc_touch", "外壳纤维粗糙，沉甸甸的。"),
            ("desc_listen", "摇晃时能听到水声。"),
        ],
    },
    {
        "prototype_key": "berry",
        "prototype_parent": ("plantae_rosaceae_rubus", "plantpart_fruit"),
        "key": "浆果",
        "attrs": [
            ("can_eat", True), ("hunger_restore", 5),
            ("desc_look", "一把鲜红的浆果，表面覆盖着细密的绒毛。"),
            ("desc_smell", "浆果散发着浓郁的甜香。"),
            ("desc_touch", "浆果软软的，捏起来有弹性。"),
            ("desc_listen", "你轻轻捏了捏浆果，果肉发出细微的噗噗声。"),
            ("desc_taste", "果汁在口中爆开，甜中带酸。"),
        ],
    },
    {
        "prototype_key": "shellfish_item",
        "prototype_parent": ("animalia_mollusca_bivalvia", "animalpart_meat"),
        "key": "海贝肉",
        "attrs": [
            ("can_eat", True), ("hunger_restore", 5),
            ("desc_look", "一块贝肉，色泽白嫩。"),
            ("desc_smell", "贝肉散发着淡淡的海水咸腥味，隐约有股鲜甜的气息。"),
            ("desc_taste", "鲜咸的海味，嚼起来滑嫩Q弹。"),
        ],
    },
    {
        "prototype_key": "fresh_water_item",
        "prototype_parent": "gb_1802",
        "key": "淡水",
        "attrs": [
            ("can_drink", True), ("thirst_restore", 20),
            ("desc_look", "清澈的液体，没有颜色。"),
            ("desc_smell", "几乎闻不到气味，只有一丝水汽。"),
            ("desc_taste", "清甜甘冽。"),
        ],
    },
    {
        "prototype_key": "hot_water_item",
        "prototype_parent": "gb_1802",
        "key": "热水",
        "attrs": [
            ("can_drink", True), ("thirst_restore", 20),
            ("desc_look", "冒着热气的清水，水面上飘着淡淡的白雾。"),
            ("desc_smell", "温热的水汽带着纯净的水味。"),
            ("desc_taste", "温热的清水入喉，暖意从胃中散开。"),
        ],
    },
    {
        "prototype_key": "salt_water_item",
        "prototype_parent": "gb_1622",
        "key": "海水",
        "attrs": [
            ("can_drink", True), ("thirst_restore", -5),
            ("desc_look", "碧蓝的海水。"),
            ("desc_smell", "海水散发着咸湿的海腥味，浓烈的盐分气息直冲鼻腔。"),
            ("desc_taste", "咸涩苦腥。"),
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # 石刃业务闭环新增 prototype
    # ══════════════════════════════════════════════════════════════════════

    # ── 配方中间层（1 个）──
    {
        "prototype_key": "recipe_base",
        "prototype_parent": "non_living",
        "key": "配方",
        "attrs": [
            ("desc_look", "一张写满制作步骤的配方。"),
            ("desc_smell", "配方散发着干燥的石头或树叶气息，上面刻写的图案散发着淡淡的尘土味。"),
            ("build_location", "inventory"),    # 产出位置：inventory(默认)/room/container
            ("duration", 0),                    # 制作时长（秒），0=即时
            ("requires", []),                   # 前置条件列表
            ("environment", None),              # 环境依赖
        ],
    },

    # ── 配方收藏夹 ──
    {
        "prototype_key": "recipe_book",
        "prototype_parent": "non_living",
        "key": "配方收藏夹",
        "typeclass": "typeclasses.objects.Object",
        "locks": "get:false();drop:false()",
        "tags": [("from_prototype", "recipe_book"), ("recipe_book", "system")],
        "attrs": [
            ("is_recipe_book", True),
        ],
    },

    # ── 系统配置基类 prototype ──
    # 纯数据容器，不可拾取/丢弃/可见，供系统运行时读取配置
    {
        "prototype_key": "system_config",
        "prototype_parent": "non_living",
        "key": "_system_config",
        "locks": "get:false();drop:false();view:false()",
        "attrs": [
            ("system_config", True),
        ],
    },

    # ── cook 配方映射表（system_config 子类）──
    # 菜肴名 → 配方模板 + 水产食材 的映射配置
    # cook 指令运行时读取此表，将菜肴名解析为配方模板和具体食材
    {
        "prototype_key": "cook_recipe_map",
        "prototype_parent": "system_config",
        "key": "_cook_recipe_map",
        "attrs": [
            # 非模板配方：菜肴名 → recipe prototype_key
            ("static_recipes", {
                "烤肉": "recipe_roast_meat",
                "沸水": "recipe_boilwater",
                "煮盐": "recipe_boilsalt",
            }),
            # 模板配方定义：recipe + 菜肴名生成模式
            ("templates", [
                {"recipe": "recipe_roast_aquatic", "pattern": "烤{dishes_name}"},
                {"recipe": "recipe_tasty_roast_aquatic", "pattern": "鲜美的烤{dishes_name}"},
                {"recipe": "recipe_aquatic_soup", "pattern": "{dishes_name}汤"},
                {"recipe": "recipe_tasty_aquatic_soup", "pattern": "鲜美的{dishes_name}汤"},
            ]),
            # 水产 prototype_key 列表（模板配方的变量食材）
            ("aquatics", [
                "mudskipper", "mangrove_shrimp", "mud_crab", "mangrove_clam", "sea_slug",
                "grouper", "spiny_lobster", "reef_crab", "oyster", "sea_snail",
                "tilapia", "river_shrimp", "stream_crab", "freshwater_mussel", "pond_snail",
            ]),
        ],
    },

    # ── 配方终端（1 个）──
    {
        "prototype_key": "recipe_stone_blade",
        "prototype_parent": "recipe_base",
        "key": "石刃配方",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "将燧石或黑曜石打磨成锋利的石刃"),
            ("background", "用燧石或黑曜石可以敲打出锋利的刃口——这是最古老的工具制作方法。"),
            ("build_location", "inventory"),
            ("output", "stone_blade"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "flint", "count": 1, "destroy_chance": 0},
                    {"prototype": "obsidian", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("output_overrides", [
                {"material": "flint", "attack": 2, "dur": 20},
                {"material": "obsidian", "attack": 4, "dur": 35},
            ]),
            ("duration", 5),
            ("process_descs", [
                {"desc": "你拿起燧石，用另一块石头仔细敲打边缘。", "repeat": 1},
                {"desc": "你在石头边缘反复打磨……", "repeat": 3},
                {"desc": "用指腹试了试刃口，还不够锋利。", "repeat": 1},
                {"desc": "最后一遍精磨，刃口在阳光下闪了一下。", "repeat": 1},
            ]),
            ("desc_look", "一块扁平的石片，表面刻着敲打石器的简单图案。"),
            ("desc_smell", "石片配方散发着干燥的矿物气息，刻痕处有淡淡的石粉味。"),
        ],
        "locks": "use:has_materials()",
    },

    # ── 非生物终端（5 个）──
    # 石刃（工具）
    {
        "prototype_key": "stone_blade",
        "prototype_parent": "non_living",
        "key": "石刃",
        "attrs": [
            ("tool_type", "cutting"),
            ("dur", 20),
            ("attack", 2),
            ("desc_look", "一片锋利的石刃，边缘经过精心敲打成型。"),
            ("desc_smell", "石刃散发着干燥的矿物气息，刃口处有一股淡淡的粉尘味。"),
            ("desc_touch", "石刃的刃口锋利得能划破手指，背面粗糙但握持处被打磨得贴合手掌。"),
        ],
    },
    # 碎石堆（资源来源）
    {
        "prototype_key": "rubble",
        "prototype_parent": "non_living",
        "key": "碎石堆",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "flint", "chance": 0.2, "method": "search",
                 "success_desc": "你翻开碎石，发现了一块黑色的燧石。",
                 "fail_desc": "翻遍了碎石，没找到可用的燧石。"},
                {"prototype": "obsidian", "chance": 0.1, "method": "search",
                 "success_desc": "你在碎石间发现了一块漆黑的黑曜石！",
                 "fail_desc": "翻遍了碎石，没找到黑曜石。"},
                {"prototype": "stone", "chance": 0.4, "method": "search",
                 "success_desc": "你从碎石堆里挑出一块合适的石块。",
                 "fail_desc": "碎石堆里没有合适的石块。"},
            ]),
            ("desc_look", "一堆大小不一的碎石，夹杂着黑色的岩石碎片。"),
            ("desc_smell", "干燥的尘土味混合着火山岩的矿物气息，空气中飘着一股淡淡的硫磺味。"),
            ("desc_touch", "碎石表面粗粝硌手，有些石片边缘锋利得能割破皮肤。"),
            ("desc_listen", "风吹过碎石坡，石子相互碰撞发出细碎的哗啦声。"),
        ],
    },
    # 燧石（材料）
    {
        "prototype_key": "flint",
        "prototype_parent": "non_living",
        "key": "燧石",
        "attrs": [
            ("item_type", "solid"),
            ("desc_look", "一块深黑色的燧石，断口锋利，泛着玻璃般的光泽。"),
            ("desc_smell", "燧石有一股干燥的矿物气味，靠近闻能嗅到石头特有的冷硬气息。"),
            ("desc_touch", "燧石冰冷沉手，断口锋利如刀刃，指腹能感受到玻璃般的平滑质感。"),
        ],
    },
    # 黑曜石（材料）
    {
        "prototype_key": "obsidian",
        "prototype_parent": "non_living",
        "key": "黑曜石",
        "attrs": [
            ("item_type", "solid"),
            ("desc_look", "一块漆黑的黑曜石，断面如镜面般光滑，边缘锋利得能割破皮肤。"),
            ("desc_smell", "黑曜石几乎无味，凑近闻只有一丝冷冽的矿物气息，像火山岩深处凝固的空气。"),
            ("desc_touch", "黑曜石冰凉光滑，断面反射着光芒，边缘锋利如剃刀。"),
        ],
    },
    # 石块（材料）
    {
        "prototype_key": "stone",
        "prototype_parent": "non_living",
        "key": "石块",
        "attrs": [
            ("item_type", "solid"),
            ("desc_look", "一块灰白色的石块，表面粗糙，握在手里沉甸甸的。"),
            ("desc_smell", "石块带着干燥的泥土气息，表面附着着一层淡淡的尘土味。"),
            ("desc_touch", "石块表面粗糙坑洼，握在手里沉甸甸的，边角硌手。"),
        ],
    },

    # ── plantpart 中间层（3 个）──
    {
        "prototype_key": "plantpart_flesh",
        "prototype_parent": "plantpart",
        "key": "果肉",
    },
    {
        "prototype_key": "plantpart_shell",
        "prototype_parent": "plantpart",
        "key": "果壳",
    },
    {
        "prototype_key": "plantpart_stem",
        "prototype_parent": "plantpart",
        "key": "茎",
    },

    # ── plantpart 终端（3 个）──
    {
        "prototype_key": "coconut_meat",
        "prototype_parent": ("plantae_arecaceae_cocos_nucifera", "plantpart_flesh"),
        "key": "椰肉",
        "attrs": [
            ("can_eat", True), ("hunger_restore", 20),
            ("desc_look", "一块雪白的椰肉，散发着淡淡的椰香。"),
            ("desc_smell", "雪白的椰肉散发着浓郁的椰奶甜香。"),
            ("desc_touch", "椰肉触感软糯，像一块温润的白玉，微微渗出透明的椰汁。"),
            ("desc_taste", "入口即化，满嘴椰香，甜而不腻，回味悠长。"),
        ],
    },
    {
        "prototype_key": "coconut_shell",
        "prototype_parent": ("plantae_arecaceae_cocos_nucifera", "plantpart_shell"),
        "key": "椰壳",
        "attrs": [
            ("item_type", "solid"),
            ("is_container", True),
            ("container_capacity", -1),
            ("vessel_content", None),
            ("supported_contents", ["fresh_water_item", "salt_water_item", "dirty_water_item"]),
            ("desc_look", "一个被切开的椰壳，切口平整，内壁光滑干净，外壳纤维蓬松粗糙，底部弧度平缓。"),
            ("desc_smell", "椰壳内壁残留着淡淡的椰奶甜香，外壳的纤维散发着干燥的木质气息。"),
            ("desc_touch", "椰壳内壁光滑温润，外壳纤维粗糙，整个椰壳轻巧但结实。"),
            ("desc_listen", "你用手指敲了敲椰壳，发出空洞的笃声。"),
        ],
    },
    {
        "prototype_key": "vine",
        "prototype_parent": "plantpart_stem",
        "key": "藤蔓",
        "attrs": [
            ("item_type", "fiber"),
            ("cut_into", "vine_strip"),
            ("cut_products", ["vine_bark", "vine_bark", "vine_bark", "vine_bark"]),
            ("desc_look", "一截结实的藤蔓，柔韧而有韧性。"),
            ("desc_smell", "藤蔓散发着新鲜的草木清香，刚割下的截面有一股淡淡的青涩味。"),
            ("desc_touch", "藤蔓表面粗糙，握在手里很结实。"),
        ],
    },
    {
        "prototype_key": "water_vine",
        "prototype_parent": "plantpart_stem",
        "key": "水藤",
        "attrs": [
            ("item_type", "fiber"),
            ("can_drink", True),
            ("thirst_restore", 10),
            ("becomes_on_consume", "vine"),
            ("desc_look", "一截粗大的藤蔓，切口处渗出清澈的水滴。"),
            ("desc_smell", "水藤散发着淡淡的草木清香，水珠处有一股甘甜的气息。"),
            ("desc_touch", "藤蔓表面湿润冰凉，挤压时有水从切口渗出。"),
        ],
    },

    # ── 椰壳状态变体（2 个）──
    {
        "prototype_key": "cut_coconut",
        "prototype_parent": "coconut_shell",
        "key": "切开的椰子",
        "attrs": [
            ("can_drink", True), ("thirst_restore", 20),
            ("initial_contents", ["coconut_meat"]),
            ("desc_look", "一个被切开的椰壳，露出雪白的椰肉和清澈的椰汁。"),
            ("desc_smell", "浓郁的椰奶香气扑面而来。"),
            ("desc_touch", "切面光滑，白色的椰肉触感细腻如凝脂，椰壳内壁温润潮湿。"),
            ("desc_listen", "你摇晃切开的椰子，椰汁在壳内轻轻晃荡。"),
            ("desc_taste", "椰汁清甜爽口。"),
        ],
    },
    {
        "prototype_key": "coconut_meat_shell",
        "prototype_parent": "coconut_shell",
        "key": "椰肉壳",
        "attrs": [
            ("initial_contents", ["coconut_meat"]),
            ("desc_look", "一个切开的椰壳，椰汁已经喝完了，内壁附着雪白的椰肉。"),
            ("desc_smell", "椰壳内壁残留着淡淡的椰奶甜香，雪白的椰肉散发着浓郁甜味。"),
            ("desc_touch", "椰壳内壁光滑温润，椰肉触感软糯。"),
            ("desc_listen", "你摇晃椰肉壳，听不到水声。"),
        ],
    },

    # ── COL 中间层（23 个）──
    # 百合纲下新增
    {"prototype_key": "plantae_poales", "prototype_parent": "plantae_liliopsida", "key": "禾本目"},
    {"prototype_key": "plantae_flagellariaceae", "prototype_parent": "plantae_poales", "key": "鞭藤科"},
    {"prototype_key": "plantae_flagellaria", "prototype_parent": "plantae_flagellariaceae", "key": "鞭藤属"},
    {"prototype_key": "plantae_arecaceae_calamus", "prototype_parent": "plantae_arecaceae", "key": "省藤属"},
    # 木兰纲下新增
    {"prototype_key": "plantae_fabales", "prototype_parent": "plantae_magnoliopsida", "key": "豆目"},
    {"prototype_key": "plantae_fabaceae", "prototype_parent": "plantae_fabales", "key": "豆科"},
    {"prototype_key": "plantae_pueraria", "prototype_parent": "plantae_fabaceae", "key": "葛属"},
    {"prototype_key": "plantae_entada", "prototype_parent": "plantae_fabaceae", "key": "植藤子属"},
    {"prototype_key": "plantae_inocarpus", "prototype_parent": "plantae_fabaceae", "key": "太平洋栗属"},
    {"prototype_key": "plantae_solanales", "prototype_parent": "plantae_magnoliopsida", "key": "茄目"},
    {"prototype_key": "plantae_convolvulaceae", "prototype_parent": "plantae_solanales", "key": "旋花科"},
    {"prototype_key": "plantae_decalobanthus", "prototype_parent": "plantae_convolvulaceae", "key": "毛茉栾藤属"},
    # 蔷薇目下新增
    {"prototype_key": "plantae_moraceae", "prototype_parent": "plantae_rosales", "key": "桑科"},
    {"prototype_key": "plantae_ficus", "prototype_parent": "plantae_moraceae", "key": "榕属"},
    # 木兰纲下新增目/科/属
    {"prototype_key": "plantae_myrtales", "prototype_parent": "plantae_magnoliopsida", "key": "桃金娘目"},
    {"prototype_key": "plantae_combretaceae", "prototype_parent": "plantae_myrtales", "key": "使君子科"},
    {"prototype_key": "plantae_terminalia", "prototype_parent": "plantae_combretaceae", "key": "榄仁属"},
    {"prototype_key": "plantae_malpighiales", "prototype_parent": "plantae_magnoliopsida", "key": "金虎尾目"},
    {"prototype_key": "plantae_calophyllaceae", "prototype_parent": "plantae_malpighiales", "key": "红厚壳科"},
    {"prototype_key": "plantae_calophyllum", "prototype_parent": "plantae_calophyllaceae", "key": "红厚壳属"},
    {"prototype_key": "plantae_ericales", "prototype_parent": "plantae_magnoliopsida", "key": "杜鹃花目"},
    {"prototype_key": "plantae_lecythidaceae", "prototype_parent": "plantae_ericales", "key": "玉蕊科"},
    {"prototype_key": "plantae_barringtonia", "prototype_parent": "plantae_lecythidaceae", "key": "玉蕊属"},

    # ── 生物终端：藤本植物（5 个）──
    {
        "prototype_key": "vine_plant_1",
        "prototype_parent": "plantae_flagellaria",
        "key": "鞭藤",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.3, "method": "search",
                 "success_desc": "你在藤蔓间摸索，枝杈间缠着一截脱落的藤条，粗细均匀。",
                 "fail_desc": "藤蔓缠得太紧，徒手扯不下来。"},
                {"prototype": "vine_strip", "chance": 0.9, "method": "cut",
                 "success_desc": "你用石刃从藤蔓上剥下了一根藤条。"},
                {"prototype": "vine_bark", "count": 4, "chance": 0.9, "method": "cut",
                 "success_desc": "你剥下了几条藤条皮。"},
                {"prototype": "water_vine", "chance": 0.15, "method": "search",
                 "success_desc": "你拨开藤蔓，发现一根切口处不断渗水的粗藤。",
                 "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [{"prototype": "vine", "count": 3}]),
            ("desc_look", "一丛粗壮的藤本植物，长长的藤鞭攀附在周围的树上。"),
            ("desc_smell", "鞭藤散发着青草的清新气息，叶片揉碎后有一股辛辣的草木味。"),
            ("desc_touch", "鞭藤表面光滑坚韧，握在手里像一条结实的绳索。"),
            ("desc_listen", "风穿过鞭藤丛，藤条相互摩擦发出吱吱嘎嘎的声响。"),
        ],
    },
    {
        "prototype_key": "vine_plant_2",
        "prototype_parent": "plantae_arecaceae_calamus",
        "key": "白藤",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.3, "method": "search",
                 "success_desc": "你在白藤间找到一截松动的藤条，根部已经从树皮上脱开。",
                 "fail_desc": "白藤的倒刺扎手，不敢贸然拉扯。"},
                {"prototype": "vine_strip", "chance": 0.9, "method": "cut",
                 "success_desc": "你小心避开倒刺，从白藤上剥下了一根藤条。"},
                {"prototype": "vine_bark", "count": 4, "chance": 0.9, "method": "cut",
                 "success_desc": "你剥下了几条藤条皮。"},
                {"prototype": "water_vine", "chance": 0.15, "method": "search",
                 "success_desc": "你拨开藤蔓，发现一根切口处不断渗水的粗藤。",
                 "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [{"prototype": "vine", "count": 3}]),
            ("desc_look", "一丛带刺的白色藤蔓，茎上密布倒钩，攀附在树干上。"),
            ("desc_smell", "白藤带着一股潮湿的木质气息，倒刺处隐约有树脂的苦味。"),
            ("desc_touch", "白藤表面密布细小的倒钩，不戴手套握住会被扎得生疼。"),
            ("desc_listen", "藤上的叶片在风中沙沙作响，偶尔有藤条弹回拍打树干的声音。"),
        ],
    },
    {
        "prototype_key": "vine_plant_3",
        "prototype_parent": "plantae_pueraria",
        "key": "葛藤",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.3, "method": "search",
                 "success_desc": "拨开密缠的葛藤，枝杈间缠着几根脱落的藤条，截面还是新鲜的青绿色。",
                 "fail_desc": "葛藤缠绕得太密，徒手扯不动。"},
                {"prototype": "vine_strip", "chance": 0.9, "method": "cut",
                 "success_desc": "你用石刃从葛藤上剥下了一根藤条。"},
                {"prototype": "vine_bark", "count": 4, "chance": 0.9, "method": "cut",
                 "success_desc": "你剥下了几条藤条皮。"},
                {"prototype": "water_vine", "chance": 0.15, "method": "search",
                 "success_desc": "你拨开藤蔓，发现一根切口处不断渗水的粗藤。",
                 "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [{"prototype": "vine", "count": 3}]),
            ("desc_look", "大片葛藤覆盖在树冠上，粗壮的藤茎垂落下来。"),
            ("desc_smell", "葛藤散发着淡淡的豆科植物清香，混合着丛林潮湿的泥土气息。"),
            ("desc_touch", "葛藤粗壮结实，外皮粗糙但韧性十足，用力拉扯也难以扯断。"),
            ("desc_listen", "粗壮的葛藤在风中轻微摇晃，发出沉闷的吱嘎声。"),
        ],
    },
    {
        "prototype_key": "vine_plant_4",
        "prototype_parent": "plantae_entada",
        "key": "过江龙",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.25, "method": "search",
                 "success_desc": "顺着巨型藤蔓摸索，分叉处夹着几根断裂的侧枝，表面还带着叶痕。",
                 "fail_desc": "过江龙的藤蔓又粗又硬，徒手弄不断。"},
                {"prototype": "vine_strip", "chance": 0.9, "method": "cut",
                 "success_desc": "你用石刃费力地从过江龙上剥下了一根藤条。"},
                {"prototype": "vine_bark", "count": 4, "chance": 0.9, "method": "cut",
                 "success_desc": "你剥下了几条藤条皮。"},
                {"prototype": "water_vine", "chance": 0.15, "method": "search",
                 "success_desc": "你拨开藤蔓，发现一根切口处不断渗水的粗藤。",
                 "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [{"prototype": "vine", "count": 3}]),
            ("desc_look", "一条手腕粗的巨型藤蔓横跨两树之间，如同一条青龙过江。"),
            ("desc_smell", "过江龙散发着浓烈的草木气息，粗大的藤茎有一股木质苦味。"),
            ("desc_touch", "手腕粗的藤茎坚硬如木，表面的纹理像老树皮一样粗糙。"),
            ("desc_listen", "巨型藤蔓在风中缓慢摆动，发出低沉的嘎吱声，像古老的门轴。"),
        ],
    },
    {
        "prototype_key": "vine_plant_5",
        "prototype_parent": "plantae_decalobanthus",
        "key": "毛茉栾藤",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.25, "method": "search",
                 "success_desc": "拨开绒毛密布的叶片，藤蔓根部有几根松脱的，轻轻一碰就在晃。",
                 "fail_desc": "藤蔓缠得太紧，徒手扯不动。"},
                {"prototype": "vine_strip", "chance": 0.9, "method": "cut",
                 "success_desc": "你用石刃从毛茉栾藤上剥下了一根藤条。"},
                {"prototype": "vine_bark", "count": 4, "chance": 0.9, "method": "cut",
                 "success_desc": "你剥下了几条藤条皮。"},
                {"prototype": "water_vine", "chance": 0.15, "method": "search",
                 "success_desc": "你拨开藤蔓，发现一根切口处不断渗水的粗藤。",
                 "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [{"prototype": "vine", "count": 3}]),
            ("desc_look", "一丛绒毛密布的藤蔓，宽大的叶片遮住了半边树干。"),
            ("desc_smell", "毛茉栾藤散发着一种清甜的花草气息，宽大的叶片揉碎后味道更浓。"),
            ("desc_touch", "藤蔓表面覆盖着细密的绒毛，摸上去柔软但韧性很强。"),
            ("desc_listen", "绒毛密布的叶片在风中轻柔地沙沙作响，像是低声耳语。"),
        ],
    },

    # ── 生物终端：宿主大树（5 个）──
    {
        "prototype_key": "host_tree_1",
        "prototype_parent": "plantae_ficus",
        "key": "环纹榕",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.2, "method": "search",
                 "success_desc": "树干上缠着的藤蔓有几根已经松脱，根部从树皮上翘了起来。",
                 "fail_desc": "树干上的藤蔓太少，不够用。"},
                {"prototype": "fresh_moss", "chance": 0.2, "method": "search",
                 "success_desc": "树根处的苔藓长得很厚，轻轻一揭就是一大片。",
                 "fail_desc": "树根处没有找到苔藓。"},
                {"prototype": "wood_stick", "chance": 0.3, "method": "search",
                 "success_desc": "树根旁散落着几根短木棍，已经干透。",
                 "fail_desc": "树根旁没有找到木棍。"},
                {"prototype": "thick_branch", "chance": 0.15, "method": "search",
                 "success_desc": "低处的枝杈上挂着一根粗壮的断枝，够一够能够到。",
                 "fail_desc": "低处的枝杈上没有断枝。"},
            ]),
            ("defense", 2), ("hp", 20), ("hp_max", 20),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 4},
                {"prototype": "wood_stick", "count": 8},
                {"pick_one": [
                    {"prototype": "vine", "count_range": [1, 5]},
                    {"prototype": "fresh_moss", "count_range": [1, 5]},
                ]},
            ]),
            ("desc_look", "一棵高大的榕树，树干上有明显的环状纹路，气根和藤蔓缠绕其间。"),
            ("desc_smell", "榕树散发着沉稳的木质香气，气根间弥漫着潮湿的苔藓味道。"),
            ("desc_touch", "环纹榕的树皮粗糙厚实，手指能抠进深深的纹路里，表面覆着滑腻的苔藓。"),
            ("desc_listen", "风吹过巨大的树冠，枝叶沙沙作响，气根在风中轻轻摇摆。"),
        ],
    },
    {
        "prototype_key": "host_tree_2",
        "prototype_parent": "plantae_terminalia",
        "key": "榄仁树",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.2, "method": "search",
                 "success_desc": "榄仁树纵裂的树皮间卡着几根藤蔓，颜色已经发枯，有一端松脱垂着。",
                 "fail_desc": "树干光溜溜的，没找到藤蔓。"},
                {"prototype": "fresh_moss", "chance": 0.2, "method": "search",
                 "success_desc": "榄仁树根部阴面长着一层苔藓，摸上去湿漉漉的。",
                 "fail_desc": "树根处没有找到苔藓。"},
                {"prototype": "wood_stick", "chance": 0.3, "method": "search",
                 "success_desc": "落叶层下面压着几根枯枝，掰开来正好是木棍。",
                 "fail_desc": "落叶层下面没有找到木棍。"},
                {"prototype": "thick_branch", "chance": 0.15, "method": "search",
                 "success_desc": "榄仁树中层枝杈上搭着一根断枝，摇一摇就掉下来了。",
                 "fail_desc": "枝杈上没有断枝。"},
            ]),
            ("defense", 2), ("hp", 20), ("hp_max", 20),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 4},
                {"prototype": "wood_stick", "count": 8},
                {"pick_one": [
                    {"prototype": "vine", "count_range": [1, 5]},
                    {"prototype": "fresh_moss", "count_range": [1, 5]},
                ]},
            ]),
            ("desc_look", "一棵枝叶层叠的榄仁树，树冠如伞般展开，藤蔓攀附在低处的枝干上。"),
            ("desc_smell", "榄仁树散发着淡淡的树脂清香，落叶在地面上发酵出微甜的泥土气息。"),
            ("desc_touch", "榄仁树的树皮纵裂成薄片，摸上去干燥粗糙，容易剥落。"),
            ("desc_listen", "层叠的枝叶在风中发出绵密的沙沙声，偶尔有干枯的叶片飘落。"),
        ],
    },
    {
        "prototype_key": "host_tree_3",
        "prototype_parent": "plantae_calophyllum",
        "key": "红厚壳",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.2, "method": "search",
                 "success_desc": "红厚壳树的枝干上缠着几根藤蔓，有一根已经从树皮上松脱。",
                 "fail_desc": "这棵树上没有合适的藤蔓。"},
                {"prototype": "fresh_moss", "chance": 0.2, "method": "search",
                 "success_desc": "红厚壳树干阴面覆着一片苔藓，绿意盎然。",
                 "fail_desc": "树干上没有苔藓。"},
                {"prototype": "wood_stick", "chance": 0.3, "method": "search",
                 "success_desc": "树根旁散落着几根干枯的短枝。",
                 "fail_desc": "树根旁没有木棍。"},
                {"prototype": "thick_branch", "chance": 0.15, "method": "search",
                 "success_desc": "革质叶片间夹着一根粗壮的断枝。",
                 "fail_desc": "枝叶间没有断枝。"},
            ]),
            ("defense", 2), ("hp", 20), ("hp_max", 20),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 4},
                {"prototype": "wood_stick", "count": 8},
                {"pick_one": [
                    {"prototype": "vine", "count_range": [1, 5]},
                    {"prototype": "fresh_moss", "count_range": [1, 5]},
                ]},
            ]),
            ("desc_look", "一棵红厚壳树，深绿的革质叶片在阳光下泛着光泽，藤蔓从枝杈间垂落。"),
            ("desc_smell", "红厚壳树散发着淡淡的树脂辛香，革质叶片有一股微苦的草木味道。"),
            ("desc_touch", "红厚壳的树皮灰褐色，表面光滑坚硬，不像榕树那样容易攀爬。"),
            ("desc_listen", "革质叶片在风中互相拍打，发出清脆的啪嗒声。"),
        ],
    },
    {
        "prototype_key": "host_tree_4",
        "prototype_parent": "plantae_barringtonia",
        "key": "滨玉蕊",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.15, "method": "search",
                 "success_desc": "滨玉蕊的枝杈间垂着几根细藤，随风晃动，有一根离地面很近。",
                 "fail_desc": "这棵滨玉蕊上藤蔓很少。"},
                {"prototype": "fresh_moss", "chance": 0.2, "method": "search",
                 "success_desc": "滨玉蕊树干基部积着一层厚苔藓，水汽很足。",
                 "fail_desc": "树干基部没有苔藓。"},
                {"prototype": "wood_stick", "chance": 0.3, "method": "search",
                 "success_desc": "落果堆里夹着几根干木棍。",
                 "fail_desc": "落果堆里没有木棍。"},
                {"prototype": "thick_branch", "chance": 0.15, "method": "search",
                 "success_desc": "滨玉蕊低垂的枝条上搭着一根断枝。",
                 "fail_desc": "低垂的枝条上没有断枝。"},
            ]),
            ("defense", 2), ("hp", 20), ("hp_max", 20),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 4},
                {"prototype": "wood_stick", "count": 8},
                {"pick_one": [
                    {"prototype": "vine", "count_range": [1, 5]},
                    {"prototype": "fresh_moss", "count_range": [1, 5]},
                ]},
            ]),
            ("desc_look", "一棵滨玉蕊，巨大的花朵已经凋谢，四棱形的果实挂在枝头，少量藤蔓缠绕在树干上。"),
            ("desc_smell", "滨玉蕊树散发着淡淡的果香，是上一季花朵残留的甜蜜气息。"),
            ("desc_touch", "滨玉蕊的树皮粗糙但较薄，四棱形的果实坚硬光滑，沉甸甸的。"),
            ("desc_listen", "偶尔有果实从枝头坠落，砸在地面上发出沉闷的咕咚声。"),
        ],
    },
    {
        "prototype_key": "host_tree_5",
        "prototype_parent": "plantae_inocarpus",
        "key": "太平洋栗",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "vine", "chance": 0.15, "method": "search",
                 "success_desc": "太平洋栗树干上的地衣间缠着几根藤蔓，有的已经干枯发脆。",
                 "fail_desc": "树干上没什么藤蔓。"},
                {"prototype": "fresh_moss", "chance": 0.2, "method": "search",
                 "success_desc": "太平洋栗树干上的地衣和苔藓混生，揭下地衣就能看到苔藓。",
                 "fail_desc": "地衣下面没有苔藓。"},
                {"prototype": "wood_stick", "chance": 0.3, "method": "search",
                 "success_desc": "树冠下散落着几根枯枝，粗细正好当木棍用。",
                 "fail_desc": "树冠下没有合适的枯枝。"},
                {"prototype": "thick_branch", "chance": 0.15, "method": "search",
                 "success_desc": "浓密树冠中伸出一根断枝，用力一扯就下来了。",
                 "fail_desc": "树冠中没有断枝。"},
            ]),
            ("defense", 2), ("hp", 20), ("hp_max", 20),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 4},
                {"prototype": "wood_stick", "count": 8},
                {"pick_one": [
                    {"prototype": "vine", "count_range": [1, 5]},
                    {"prototype": "fresh_moss", "count_range": [1, 5]},
                ]},
            ]),
            ("desc_look", "一棵太平洋栗树，粗壮的树干上附着地衣和少量藤蔓，树冠浓密。"),
            ("desc_smell", "太平洋栗散发着淡淡的坚果香气，混合着地衣的潮湿气息。"),
            ("desc_touch", "太平洋栗的树皮深褐色，覆盖着片状地衣，摸上去柔软潮湿。"),
            ("desc_listen", "浓密的树冠在风中发出闷闷的沙沙声，像一面绿色的墙在呼吸。"),
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # 基础生存闭环新增 prototype
    # ══════════════════════════════════════════════════════════════════════

    # ── 新增 COL 中间层 ──
    # 芭蕉科（Musaceae）
    {"prototype_key": "plantae_zingiberales", "prototype_parent": "plantae_liliopsida", "key": "姜目"},
    {"prototype_key": "plantae_musaceae", "prototype_parent": "plantae_zingiberales", "key": "芭蕉科"},
    {"prototype_key": "plantae_musaceae_musa", "prototype_parent": "plantae_musaceae", "key": "芭蕉属"},
    {"prototype_key": "plantae_musaceae_musa_paradisiaca", "prototype_parent": "plantae_musaceae_musa", "key": "芭蕉"},
    # 旅人蕉科（Strelitziaceae）
    {"prototype_key": "plantae_strelitziaceae", "prototype_parent": "plantae_zingiberales", "key": "旅人蕉科"},
    {"prototype_key": "plantae_strelitziaceae_ravenala", "prototype_parent": "plantae_strelitziaceae", "key": "旅人蕉属"},
    # 竹亚科（Bambusoideae）
    {"prototype_key": "plantae_poaceae", "prototype_parent": "plantae_poales", "key": "禾本科"},
    {"prototype_key": "plantae_poaceae_bambusa", "prototype_parent": "plantae_poaceae", "key": "竹属"},
    {"prototype_key": "plantae_poaceae_bambusa_vulgaris", "prototype_parent": "plantae_poaceae_bambusa", "key": "竹子"},
    # 泥炭藓（Sphagnum）
    {"prototype_key": "plantae_bryophyta", "prototype_parent": "plantae", "key": "苔藓植物门"},
    {"prototype_key": "plantae_sphagnaceae", "prototype_parent": "plantae_bryophyta", "key": "泥炭藓科"},
    {"prototype_key": "plantae_sphagnaceae_sphagnum", "prototype_parent": "plantae_sphagnaceae", "key": "泥炭藓属"},

    # ── 新增 plantpart 中间层 ──
    {"prototype_key": "plantpart_leaf", "prototype_parent": "plantpart", "key": "叶"},
    {"prototype_key": "plantpart_fiber", "prototype_parent": "plantpart", "key": "纤维"},

    # ── 生长周期类型链 ──
    {
        "prototype_key": "growthcycle",
        "prototype_parent": "organism",
        "key": "生长周期",
        "attrs": [
            ("desc", "植物生长周期类型，与物种 COL 主链复合使用。"),
        ],
    },
    {
        "prototype_key": "growthcycle_sapling",
        "prototype_parent": "growthcycle",
        "key": "幼苗期",
        "locks": "get:false()",
        "attrs": [
            ("desc", "幼苗期：植物尚未成熟，防御低、血量少。"),
            ("defense", 1),
            ("hp", 12), ("hp_max", 12),
            ("chop_output", [
                {"prototype": "long_stick", "count": 1},
                {"prototype": "wood_stick", "count": 3},
                {"prototype": "tree_branch", "count": 1, "chance": 0.5},
            ]),
        ],
    },
    {
        "prototype_key": "growthcycle_young",
        "prototype_parent": "growthcycle",
        "key": "生长期",
        "locks": "get:false()",
        "attrs": [
            ("desc", "生长期：植物逐渐成熟，已有一定防御和血量。"),
            ("defense", 2),
            ("hp", 20), ("hp_max", 20),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 2},
                {"prototype": "wood_stick", "count": 1},
                {"prototype": "tree_branch", "count": 1, "chance": 0.5},
            ]),
        ],
    },

    # ── 榕树（物种本体，直接作为成熟体） ──
    {
        "prototype_key": "ficus_tree",
        "prototype_parent": "plantae_ficus",
        "key": "榕树",
        "locks": "get:false()",
        "attrs": [
            ("defense", 3),
            ("hp", 30), ("hp_max", 30),
            ("chop_output", [
                {"prototype": "log", "count": 1},
                {"prototype": "long_stick", "count": 1},
                {"prototype": "tree_branch", "count": 1, "chance": 0.5},
                {"prototype": "vine", "count": 1, "chance": 0.3},
                {"prototype": "palm_leaf", "count": 1, "chance": 0.2},
            ]),
            ("resource", [
                {"prototype": "thick_branch", "chance": 0.4, "method": "search",
                 "success_desc": "气根间卡着一根断裂的树枝，比手臂还粗，树皮上还长着苔藓。", "fail_desc": ""},
                {"prototype": "vine", "chance": 0.2, "method": "search",
                 "success_desc": "气根间缠着一根藤蔓，已经从上端断开，只连着一截树皮。", "fail_desc": ""},
            ]),
            ("locks", "get:false()"),
            ("desc_look", "一棵参天古榕，粗壮的树干上垂下无数气生根，树冠遮天蔽日。"),
            ("desc_smell", "古榕散发着沉稳浓郁的木质香气，气根间弥漫着潮湿的苔藓和泥土芬芳。"),
        ],
    },

    # ── 榕树复合对象（物种本体 × 生长周期） ──
    {
        "prototype_key": "ficus_young",
        "prototype_parent": ("ficus_tree", "growthcycle_young"),
        "key": "成长期榕树",
        "attrs": [
            ("desc_look", "一棵成长中的榕树，已有粗壮的气生根垂下，树干还不够粗壮。"),
            ("desc_smell", "成长期的榕树散发着清新的木质香气，气根间弥漫着潮湿的绿植气息。"),
        ],
    },
    {
        "prototype_key": "ficus_sapling",
        "prototype_parent": ("ficus_tree", "growthcycle_sapling"),
        "key": "榕树幼苗",
        "attrs": [
            ("desc_look", "一棵幼小的榕树，树干只有手臂粗，气生根刚刚萌出。"),
            ("desc_smell", "幼小的榕树散发着稚嫩的植物清香，新萌出的气根有一股湿润的青涩气息。"),
        ],
    },

    # ── 新增资源来源（环境对象）──
    # 杂草丛（LC-03a §7.1）
    {
        "prototype_key": "weed",
        "prototype_parent": "plantae",
        "typeclass": "survival.objects.Organism",
        "key": "杂草丛",
        "aliases": [],
        "locks": "get:false()",
        "attrs": [
            ("desc_look", "一丛低矮的杂草，叶片窄长，根部交错纠缠。"),
            ("desc_smell", "揉碎叶片能闻到一股青涩的草汁味。"),
            ("resource", [
                {"prototype": "dry_grass", "chance": 0.15, "method": "search",
                 "success_desc": "杂草丛深处藏着一把干枯发脆的草叶。", "fail_desc": ""},
                {"prototype": "fresh_grass", "chance": 0.8, "method": "search",
                 "success_desc": "拨开草丛，几簇青绿的草叶从根部露出来，比周围的杂草嫩得多。", "fail_desc": "你拨弄了杂草丛，没什么收获。"},
                {"prototype": "fresh_grass", "chance": 0.8, "method": "cut",
                 "success_desc": "你割下了一些新鲜的草。", "fail_desc": ""},
            ]),
            ("defense", 0),
            ("hp", 1),
            ("hp_max", 1),
        ],
    },
    # 苔藓丛（LC-03a §7.2）
    {
        "prototype_key": "moss_plant",
        "prototype_parent": "plantae_sphagnaceae_sphagnum",
        "typeclass": "survival.objects.Organism",
        "key": "苔藓丛",
        "aliases": [],
        "locks": "get:false()",
        "attrs": [
            ("desc_look", "一片密实的苔藓，贴着潮湿的地面铺开，深浅不一的绿色层层叠叠。"),
            ("desc_smell", "潮湿的泥土气息混合着一股淡淡的蘑菇味。"),
            ("resource", [
                {"prototype": "dry_moss", "chance": 0.15, "method": "search",
                 "success_desc": "苔藓丛底部藏着一团已经干透的苔藓，轻轻一捏就碎成粉末。", "fail_desc": ""},
                {"prototype": "fresh_moss", "chance": 0.8, "method": "search",
                 "success_desc": "你小心地取下了一团苔藓。", "fail_desc": "你翻看了苔藓丛，没什么收获。"},
            ]),
        ],
    },
    {
        "prototype_key": "palm_sapling",
        "prototype_parent": "plantae_arecaceae",
        "key": "棕榈树苗",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "palm_leaf", "chance": 0.4, "method": "search",
                 "success_desc": "低垂的棕榈叶间，有几片已经从叶柄处断开，只差一点就要落下来。", "fail_desc": "你查看了棕榈树，没有发现什么。"},
                {"prototype": "palm_leaf", "chance": 0.6, "method": "cut",
                 "success_desc": "", "fail_desc": ""},
            ]),
            ("defense", 0), ("hp", 1), ("hp_max", 1),
            ("desc_look", "一棵矮小的棕榈树苗，叶子触手可及。"),
            ("desc_smell", "棕榈树苗散发着清新的绿叶气息，新叶处有一股淡淡的甘甜。"),
        ],
    },
    {
        "prototype_key": "banana_tree",
        "prototype_parent": "plantae_musaceae_musa_paradisiaca",
        "key": "香蕉植株",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "banana_leaf", "chance": 0.4, "method": "search",
                 "success_desc": "宽大的蕉叶层层叠叠，有几片已经从茎上脱落，夹在叶鞘之间。", "fail_desc": "你查看了香蕉植株，没有发现什么。"},
                {"prototype": "banana", "chance": 0.08, "method": "search",
                 "success_desc": "叶鞘缝隙间露出一截黄色的果皮，几根香蕉挤在一起。", "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [
                {"prototype": "banana", "count": 5},
                {"prototype": "banana_leaf", "count": 10},
            ]),
            ("desc_look", "一棵香蕉植株，宽大的叶子在微风中摆动。"),
            ("desc_smell", "香蕉植株散发着热带植物特有的湿润草香，偶尔飘来一丝若有若无的果甜。"),
        ],
    },
    {
        "prototype_key": "banana_plant",
        "prototype_parent": "plantae_musaceae_musa_paradisiaca",
        "key": "芭蕉植株",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "banana_leaf", "chance": 0.4, "method": "search",
                 "success_desc": "芭蕉叶层层叠叠，有几片已经从茎上脱落，夹在叶鞘之间。", "fail_desc": "你查看了芭蕉植株，没有发现什么。"},
                {"prototype": "banana", "chance": 0.08, "method": "search",
                 "success_desc": "拨开宽大的叶片，果串上还挂着几根芭蕉，表皮已经泛黄。", "fail_desc": ""},
            ]),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [
                {"prototype": "banana", "count": 5},
                {"prototype": "banana_leaf", "count": 10},
            ]),
            ("desc_look", "一丛芭蕉，宽大的叶子遮出一片阴凉。"),
            ("desc_smell", "芭蕉叶散发出湿润清凉的草木气息，阴凉处弥漫着泥土和腐叶混合的微甜味道。"),
        ],
    },
    {
        "prototype_key": "travelers_palm",
        "prototype_parent": "plantae_strelitziaceae_ravenala",
        "key": "旅人蕉",
        "locks": "get:false()",
        "attrs": [
            ("thirst_restore", 20),
            ("desc_look", "一棵高大的旅人蕉，扇形排列的叶片如同孔雀开屏，叶鞘间积着清澈的水。"),
            ("desc_smell", "旅人蕉散发着清新的热带植物气息，叶鞘处飘来一股若有若无的甘甜水味。"),
            ("desc_touch", "旅人蕉的叶鞘圆润饱满，轻轻按压能感觉到里面有液体晃动。"),
            ("desc_listen", "风吹过扇形叶片，发出有节奏的哗哗声，像流水拍打石岸。"),
        ],
    },
    {
        "prototype_key": "bamboo",
        "prototype_parent": "plantae_poaceae_bambusa_vulgaris",
        "key": "竹子",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "bamboo_twig", "chance": 0.4, "method": "search",
                 "success_desc": "竹丛底部散落着几根断落的竹枝，表面还泛着新鲜的青绿色。", "fail_desc": "你查看了竹子，没有发现什么。"},
                {"prototype": "bamboo_twig", "chance": 0.4, "method": "cut",
                 "success_desc": "", "fail_desc": ""},
                {"prototype": "long_bamboo_stick", "chance": 0.05, "method": "search",
                 "success_desc": "竹子根部积着一层落叶，落叶下面压着一根修长的竹棍，颜色已经发黄。", "fail_desc": ""},
            ]),
            ("cut_defense", 1), ("cut_hp", 1),
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [
                {"prototype": "long_bamboo_stick", "count": 1},
                {"prototype": "bamboo_twig", "count": 2},
            ]),
            ("desc_look", "一丛翠绿的竹子，挺拔而修长。"),
            ("desc_smell", "竹子散发着清冽的竹香，空气中弥漫着一股淡雅的草木清香。"),
        ],
    },
    {
        "prototype_key": "dirty_water_source",
        "prototype_parent": "gb_1802",
        "key": "脏水源",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "dirty_water_item", "chance": 1.0, "success_desc": "你发现水面下有一层浑浊的沉淀，水色泛黄。"},
            ]),
            ("desc_look", "一滩泛着黄褐色的积水，水面上漂着几片枯叶，水底积着一层不明沉淀。"),
            ("desc_smell", "一股刺鼻的酸腐气味混合着泥土的腥气，让人不由皱眉。"),
            ("desc_touch", "水面温吞黏腻，指尖触上去有一层滑腻的薄膜感。"),
            ("desc_listen", "偶尔有气泡从水底咕噜噜冒上来，发出闷闷的声响。"),
            ("desc_taste", "一股土腥味直冲鼻腔，舌根泛起涩苦的回味。"),
        ],
    },
    # 浑浊溪流（溪流中游统一水源，Bug3 修复）
    {
        "prototype_key": "murky_stream",
        "prototype_parent": "gb_1802",
        "key": "浑浊的溪流",
        "locks": "get:false()",
        "attrs": [
            ("resource", [
                {"prototype": "dirty_water_item", "chance": 1.0,
                 "success_desc": "你发现溪水在这里变得浑浊，水底泛着一层不自然的黄褐色沉淀。"},
            ]),
            ("desc_look", "溪水在这里变得浑浊，水面泛着不自然的黄色，隐约可以闻到一股土腥味。"),
            ("desc_smell", "水汽中夹杂着泥腥和腐殖质的酸涩气息，不像上游那般清冽。"),
            ("desc_touch", "溪水触感温吞黏腻，不像上游那样冰凉清透，指缝间能感到细密的悬浮颗粒。"),
            ("desc_listen", "水声变得沉闷，像是被什么东西堵住了嗓音，偶尔有气泡咕嘟冒上来的声响。"),
            ("desc_taste", "舌尖一沾就尝到一股土腥的涩味，舌根发苦。"),
        ],
    },
    # 山地湖泊统一水源（Bug5 修复：合并淡水和水产）
    {
        "prototype_key": "mountain_lake_water",
        "prototype_parent": "gb_1802",
        "key": "清澈湖水",
        "locks": "get:false()",
        "attrs": [
            # 资源组1：饮水资源（fill/search 盛取淡水）
            ("resource", [
                {"prototype": "fresh_water_item", "chance": 1.0},
            ]),
            # 资源组2：水产资源（捕鱼笼专用，search 不可见）
            ("fish_resource", [
                {"prototype": "tilapia", "chance": 0.4},
                {"prototype": "river_shrimp", "chance": 0.35},
                {"prototype": "stream_crab", "chance": 0.2},
                {"prototype": "freshwater_mussel", "chance": 0.3},
                {"prototype": "pond_snail", "chance": 0.3},
            ]),
            ("desc_look", "清澈的水面泛着粼粼波光。"),
            ("desc_smell", "清新的水汽扑面而来。"),
            ("desc_taste", "清甜，没有异味。"),
        ],
    },

    # ── 新增原材料 ──
    # 脏水
    {
        "prototype_key": "dirty_water_item",
        "prototype_parent": "gb_1802",
        "key": "脏水",
        "attrs": [
            ("can_drink", True), ("thirst_restore", 15), ("stamina_cost", 20),
            ("vessel_only", True),
            ("desc_look", "浑浊的液体，泛着不自然的黄褐色，散发出一股刺鼻的酸腐气味。"),
            ("desc_smell", "一股浓重的泥土腥气混合着腐烂植物的酸涩，让人本能地想移开鼻子。"),
            ("desc_touch", "液体黏腻温吞，指腹搓捻能感到细密的悬浮颗粒。"),
            ("desc_taste", "入口一股土腥的涩味直冲喉咙，舌根发苦，喉咙不自觉地想把它吐出来。"),
        ],
    },
    # 木质材料
    {
        "prototype_key": "wood_stick",
        "prototype_parent": "plantpart_stem",
        "key": "木棍",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 1),
            ("desc_look", "一根手腕粗的木棍，树皮剥落大半，露出淡黄色的木质。断裂面参差不齐，有几道劈裂的痕迹。"),
            ("desc_smell", "干燥的木棍散发着淡淡的木头清香。"),
        ],
    },
    {
        "prototype_key": "tree_branch",
        "prototype_parent": "plantpart_stem",
        "key": "树枝",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 1),
            ("desc_look", "一根手指粗细的树枝，树皮干裂，折断面露出白嫩的木质。"),
            ("desc_smell", "细树枝带着一股干燥的木质气息，树皮处隐约残留着树脂的味道。"),
        ],
    },
    {
        "prototype_key": "long_stick",
        "prototype_parent": "plantpart_stem",
        "key": "长木棍",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 2),
            ("defense", 0), ("hp", 1), ("hp_max", 1),
            ("chop_output", [{"prototype": "wood_stick", "count": 2}]),
            ("desc_look", "一根笔直的长木棍，约一人多高，粗细均匀，木质坚硬。"),
            ("desc_smell", "长木棍散发着干燥木材特有的清香，表面微微泛着木质油脂的气息。"),
        ],
    },
    {
        "prototype_key": "log",
        "prototype_parent": "plantpart_stem",
        "key": "原木",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 4),
            ("desc_look", "一截比大腿还粗的原木，截面上能看到细密的年轮。"),
            ("desc_smell", "原木散发着浓重的木质香气，截面处渗出的树液带着微微的松脂辛香。"),
        ],
    },
    # 火绒
    {
        "prototype_key": "dry_grass",
        "prototype_parent": "plantpart_leaf",
        "key": "干燥的草",
        "attrs": [
            ("item_type", "fiber"), ("tinder", True),
            ("desc_look", "一把干枯发脆的草叶，轻轻一搓就碎成细末，触感干燥蓬松。"),
            ("desc_smell", "干草散发着烘烤过的太阳气息，有一股干燥温暖的稻草味。"),
        ],
    },
    {
        "prototype_key": "dry_moss",
        "prototype_parent": "plantpart_leaf",
        "key": "干燥的苔藓",
        "attrs": [
            ("item_type", "fiber"), ("tinder", True),
            ("desc_look", "一团干燥发脆的苔藓，轻轻捏碎后变成细密的粉末，手感蓬松如棉絮。"),
            ("desc_smell", "干苔藓有一股尘土般的干燥气息，隐约残留着泥土和蘑菇的微弱芬芳。"),
        ],
    },
    # 新鲜材料（干燥前态，LC-03a §7.3/§7.4）
    # 注意：prototype 的 exec 字段在 spawner 事务内无法持久化脚本，
    # 改为 spawn 后在代码中调用 attach_drying_timer(obj)。
    {
        "prototype_key": "fresh_grass",
        "prototype_parent": "plantpart_leaf",
        "key": "新鲜的草",
        "aliases": [],
        "locks": "get:true()",
        "attrs": [
            ("desc_look", "刚拔下的草叶，根部还沾着湿润的泥土。"),
            ("desc_smell", "断面散出一股青涩的草汁味。"),
        ],
    },
    {
        "prototype_key": "fresh_moss",
        "prototype_parent": "plantpart_leaf",
        "key": "新鲜的苔藓",
        "aliases": [],
        "locks": "get:true()",
        "attrs": [
            ("desc_look", "一团深绿色的苔藓，表面水珠密布，颜色比干燥时深了许多。"),
            ("desc_smell", "潮湿的泥土气息混合着蘑菇的微酸。"),
        ],
    },
    # 石材
    {
        "prototype_key": "small_stone",
        "prototype_parent": "non_living",
        "key": "小石头",
        "attrs": [
            ("item_type", "solid"),
            ("desc_look", "一块拳头大小的灰白色石头，表面光滑。"),
            ("desc_smell", "小石头几乎无味，凑近闻只有一丝冰冷的矿物气息。"),
        ],
    },
    # 叶片材料
    {
        "prototype_key": "palm_leaf",
        "prototype_parent": "plantpart_leaf",
        "key": "棕榈叶",
        "attrs": [
            ("item_type", "fiber"),
            ("desc_look", "一片半人高的棕榈叶，叶脉粗壮，边缘呈锯齿状。"),
            ("desc_smell", "棕榈叶散发着清新的绿叶气息，叶脉处隐约有淡淡的青草甜味。"),
        ],
    },
    {
        "prototype_key": "banana_leaf",
        "prototype_parent": "plantpart_leaf",
        "key": "香蕉叶",
        "attrs": [
            ("item_type", "fiber"),
            ("desc_look", "一片比人还宽的芭蕉叶，叶面光滑，主脉从中间贯穿到底。"),
            ("desc_smell", "香蕉叶散发着热带植物特有的清新气息，隐约有一丝甘甜的果香。"),
        ],
    },
    # 食物
    {
        "prototype_key": "banana",
        "prototype_parent": ("plantae_musaceae_musa_paradisiaca", "plantpart_fruit"),
        "key": "香蕉",
        "attrs": [
            ("can_eat", True), ("hunger_restore", 8),
            ("desc_look", "一根熟透的香蕉。"),
            ("desc_smell", "香蕉散发着浓郁甜蜜的果香，熟透的果皮处香气更加浓烈。"),
        ],
    },
    # 竹材
    {
        "prototype_key": "bamboo_twig",
        "prototype_parent": ("plantae_poaceae_bambusa_vulgaris", "plantpart_stem"),
        "key": "竹枝",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 1),
            ("desc_look", "一根细竹枝条。"),
            ("desc_smell", "竹枝条散发着淡淡的竹子清香，断面处有一股清冽的草木气息。"),
        ],
    },
    {
        "prototype_key": "bamboo_stick",
        "prototype_parent": "plantpart_stem",
        "key": "竹棍",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 1),
            ("desc_look", "一截短竹棍，竹节分明，表面光滑坚韧。"),
            ("desc_smell", "竹棍散发着清新的竹香，竹节处有一股淡淡的青涩气息。"),
        ],
    },
    {
        "prototype_key": "long_bamboo_stick",
        "prototype_parent": ("plantae_poaceae_bambusa_vulgaris", "plantpart_stem"),
        "key": "长竹棍",
        "attrs": [
            ("item_type", "solid"), ("fuel_value", 2),
            ("defense", 0), ("hp", 1), ("hp_max", 1),
            ("chop_output", [{"prototype": "bamboo_stick", "count": 2}]),
            ("desc_look", "一根修长的竹棍。"),
            ("desc_smell", "长竹棍散发着淡淡的竹叶清香，手感光滑冰凉。"),
        ],
    },
    # 藤类材料
    {
        "prototype_key": "vine_strip",
        "prototype_parent": ("plantpart_stem", "plantpart_fiber"),
        "key": "藤条",
        "attrs": [
            ("item_type", "fiber"),
            ("desc_look", "一根柔韧的藤条。"),
            ("desc_smell", "藤条散发着新鲜的草木清香，剥开的纤维处有一股青涩的植物汁液味。"),
        ],
    },
    {
        "prototype_key": "vine_bark",
        "prototype_parent": ("plantpart_stem", "plantpart_fiber"),
        "key": "藤条皮",
        "attrs": [
            ("item_type", "fiber"),
            ("desc_look", "一条柔韧的藤条皮，表面粗糙但极有韧性，撕扯不断。"),
            ("desc_smell", "藤条皮散发着浓郁的草木汁液气息，新剥的纤维有一股微苦的植物味道。"),
        ],
    },
    # 粗壮树枝（成年大树 search 产出，可砍伐）
    {
        "prototype_key": "thick_branch",
        "prototype_parent": "plantpart_stem",
        "key": "粗壮树枝",
        "locks": "get:false()",
        "attrs": [
            ("defense", 1), ("hp", 5), ("hp_max", 5),
            ("chop_output", [
                {"prototype": "long_stick", "count": 1},
                {"prototype": "wood_stick", "count": 3},
                {"prototype": "tree_branch", "count": 1, "chance": 0.5},
            ]),
            ("desc_look", "一根粗壮的树枝，比手臂还粗，表面布满粗糙的树皮和苔藓，沉甸甸的。"),
            ("desc_smell", "粗壮的树枝散发着潮湿的苔藓气息和木质清香，树皮缝隙间有泥土的微甜味道。"),
        ],
    },
    # 盐
    {
        "prototype_key": "salt",
        "prototype_parent": "non_living",
        "key": "盐",
        "attrs": [
            ("item_type", "solid"), ("seasoning", True),
            ("desc_look", "一小撮白色的细小颗粒，在光线下微微闪烁。"),
            ("desc_smell", "盐几乎没有气味，凑近细闻只有一丝干燥的海风咸味。"),
        ],
    },

    # ── 新增工具 ──
    {
        "prototype_key": "stone_axe",
        "prototype_parent": "non_living",
        "key": "石斧",
        "attrs": [
            ("tool_type", "chopping"), ("attack", 5), ("dur", 30),
            ("desc_look", "一块打磨过的石片被藤条绑在木棍一端，刃口钝厚但结实。"),
            ("desc_smell", "石斧的木柄散发着干燥的木香，石刃处有淡淡的矿物粉尘味。"),
        ],
    },
    {
        "prototype_key": "obsidian_axe",
        "prototype_parent": "non_living",
        "key": "黑曜石斧",
        "attrs": [
            ("tool_type", "chopping"), ("attack", 8), ("dur", 45),
            ("desc_look", "一把锋利的黑曜石斧，刃口闪着寒光。"),
            ("desc_smell", "黑曜石斧散发着一股冷冽的矿物气息，藤条绑扎处有淡淡的草木涩味。"),
        ],
    },

    # ── 磨损生命周期链 prototype ──
    {
        "prototype_key": "worn_tool",
        "key": "磨损的工具",
        "attrs": [("dur", 0), ("worn", True)],
    },

    # ── 磨损态复合 prototype（主体 × 磨损生命周期链）──
    {
        "prototype_key": "worn_stone_blade",
        "prototype_parent": ("stone_blade", "worn_tool"),
        "key": "磨损的石刃",
        "attrs": [
            ("repair_recipe", "recipe_stone_blade"),
            ("desc_look", "刃口已经崩出好几个缺口，边缘不再锋利，石面上布满细密的裂纹。"),
            ("desc_touch", "刃口钝涩，手指划过去毫无割裂感，背面磨损得坑坑洼洼。"),
        ],
    },
    {
        "prototype_key": "worn_stone_axe",
        "prototype_parent": ("stone_axe", "worn_tool"),
        "key": "磨损的石斧",
        "attrs": [
            ("repair_recipe", "recipe_stone_axe"),
            ("desc_look", "石片刃口磨秃了，藤条绑扎处松松垮垮，木棍顶端有裂痕。"),
            ("desc_touch", "石刃钝得刮不动树皮，藤条缠得不再紧实，握柄上满是使用留下的磨痕。"),
        ],
    },
    {
        "prototype_key": "worn_obsidian_axe",
        "prototype_parent": ("obsidian_axe", "worn_tool"),
        "key": "磨损的黑曜石斧",
        "attrs": [
            ("repair_recipe", "recipe_obsidian_axe"),
            ("desc_look", "黑曜石刃口崩了几道豁口，寒光不再，藤条绑扎处发黑松脱。"),
            ("desc_touch", "刃口参差不齐，原本锋利的边缘碎裂成锯齿状，绑扎的藤条已经松弛。"),
        ],
    },

    {
        "prototype_key": "hand_drill",
        "prototype_parent": "non_living",
        "key": "手钻",
        "attrs": [
            ("tool_type", "fire_starting"),
            ("desc_look", "一根削尖的木棍插在一块带凹槽的底板上，凹槽内有焦黑的摩擦痕迹。"),
            ("desc_smell", "手钻的木杆散发着干燥的木头气味，摩擦过的部分有一股微微的焦糊味。"),
        ],
    },
    {
        "prototype_key": "weak_torch",
        "prototype_parent": "non_living",
        "key": "弱火把",
        "attrs": [
            ("tool_type", "lighting"),
            ("desc_look", "一支简陋的火把，发出微弱的光。"),
            ("desc_smell", "火把散发着干燥木柴和焦烟的气味，未点燃时有股淡淡的草木气息。"),
        ],
    },
    {
        "prototype_key": "coconut_bidon",
        "prototype_parent": "non_living",
        "key": "椰壳水壶",
        "attrs": [
            ("tool_type", "container"),
            ("is_container", True), ("container_capacity", -1),
            ("vessel_content", None),
            ("supported_contents", ["fresh_water_item", "salt_water_item", "dirty_water_item"]),
            ("desc_look", "一个椰壳被藤条编成的网兜包裹着，开口处用藤条缠紧，底部平稳。"),
            ("desc_smell", "椰壳水壶散发着椰壳残留的淡淡椰香和藤条编织的草木气息。"),
        ],
    },
    {
        "prototype_key": "chopsticks",
        "prototype_parent": "non_living",
        "key": "筷子",
        "attrs": [
            ("tool_type", "utensil"),
            ("desc_look", "一双简易的筷子。"),
            ("desc_smell", "筷子散发着淡淡的木香或竹香，没有其他异味。"),
        ],
    },
    {
        "prototype_key": "bamboo_straw",
        "prototype_parent": "non_living",
        "key": "吸管",
        "attrs": [
            ("tool_type", "utensil"),
            ("desc_look", "一根竹制吸管。"),
            ("desc_smell", "竹制吸管散发着淡淡的竹叶清香。"),
        ],
    },
    {
        "prototype_key": "fish_trap",
        "prototype_parent": "non_living",
        "key": "捕鱼笼",
        "typeclass": "survival.objects.FishTrap",
        "attrs": [
            ("tool_type", "fishing"),
            ("trap_state", "empty"),
            ("set_time", None),
            ("set_room_water", None),
            ("desc_look", "一个用藤条编织的捕鱼笼。"),
            ("desc_smell", "捕鱼笼散发着藤条的草木清香，若捕获过水产会残留淡淡的鱼腥味。"),
            ("commands", [
                {"category": "system", "key": "settrap", "path": "commands/fish.FishTrapCmdSet"},
                {"category": "system", "key": "collect", "path": "commands/fish.FishTrapCmdSet"},
            ]),
        ],
    },

    # ── 新增配方 ──
    {
        "prototype_key": "recipe_stone_axe",
        "prototype_parent": "recipe_base",
        "key": "石斧配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "将石刃绑在木棍上制成石斧"),
            ("background", "将石刃绑在木棍上，制成石斧。"),
            ("output", "stone_axe"),
            ("build_location", "inventory"),
            ("materials", [
                {"prototype": "wood_stick", "count": 1, "destroy_chance": 0},
                {"alternatives": [
                    {"prototype": "stone_blade", "count": 1, "destroy_chance": 0},
                    {"prototype": "flint", "count": 2, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "vine_bark", "count": 1, "destroy_chance": 0},
                    {"prototype": "vine", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 8),
            ("process_descs", [
                {"desc": "你开始制作石斧...", "repeat": 2},
                {"desc": "石刃牢牢地固定在木棍上了。", "repeat": 3},
                {"desc": "石斧制作完成！", "repeat": 1},
            ]),
            ("desc_look", "一块石片，上面刻着将石刃绑在木棍上的图案。"),
            ("desc_smell", "石片上的刻痕里嵌着石粉，凑近闻有一股干燥的石英气息。"),
        ],
    },
    {
        "prototype_key": "recipe_obsidian_axe",
        "prototype_parent": "recipe_base",
        "key": "黑曜石斧配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "将黑曜石绑在木棍上制成锋利的黑曜石斧"),
            ("background", "将黑曜石绑在木棍上，制成锋利的斧头。"),
            ("output", "obsidian_axe"),
            ("build_location", "inventory"),
            ("materials", [
                {"prototype": "wood_stick", "count": 1, "destroy_chance": 0},
                {"prototype": "obsidian", "count": 1, "destroy_chance": 0},
                {"alternatives": [
                    {"prototype": "vine_bark", "count": 1, "destroy_chance": 0},
                    {"prototype": "vine", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 10),
            ("process_descs", [
                {"desc": "你开始制作黑曜石斧...", "repeat": 2},
                {"desc": "黑曜石刃口锋利无比。", "repeat": 3},
                {"desc": "黑曜石斧制作完成！", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着将黑色石刃固定在木柄上的图案。"),
            ("desc_smell", "石片上有淡淡的木屑气味，是之前参照制作时留下的痕迹。"),
        ],
    },
    {
        "prototype_key": "recipe_hand_drill",
        "prototype_parent": "recipe_base",
        "key": "手钻配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "用木棍和树枝制作简易手钻"),
            ("background", "用木棍和树枝制作一个简易的手钻。"),
            ("output", "hand_drill"),
            ("build_location", "inventory"),
            ("materials", [
                {"prototype": "wood_stick", "count": 1, "destroy_chance": 0},
                {"prototype": "tree_branch", "count": 1, "destroy_chance": 0},
            ]),
            ("duration", 3),
            ("process_descs", [
                {"desc": "你开始制作手钻...", "repeat": 1},
                {"desc": "手钻制作完成。", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着两根木棍组合的图案。"),
            ("desc_smell", "石片表面冰凉光滑，散发着黑曜石特有的冷冽矿物气息。"),
        ],
    },
    {
        "prototype_key": "recipe_weak_torch",
        "prototype_parent": "recipe_base",
        "key": "弱火把配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "用藤条将可燃物绑在木棍上制成火把"),
            ("background", "用藤条将可燃物绑在木棍上，制成火把。"),
            ("output", "weak_torch"),
            ("build_location", "inventory"),
            ("materials", [
                {"prototype": "wood_stick", "count": 1, "destroy_chance": 0},
                {"alternatives": [
                    {"prototype": "vine_strip", "count": 1, "destroy_chance": 0},
                    {"prototype": "vine", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 3),
            ("process_descs", [
                {"desc": "你开始制作火把...", "repeat": 1},
                {"desc": "火把制作完成。", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着将藤条缠绕在木棍上的图案。"),
            ("desc_smell", "石片边缘有一股淡淡的焦糊味，刻痕处残留着木炭粉末。"),
        ],
    },
    {
        "prototype_key": "recipe_coconut_bidon",
        "prototype_parent": "recipe_base",
        "key": "椰壳水壶配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "用藤条将椰壳封口制成便携水壶"),
            ("background", "用藤条将椰壳封口，制成便携水壶。"),
            ("output", "coconut_bidon"),
            ("build_location", "inventory"),
            ("materials", [
                {"prototype": "coconut", "count": 1, "destroy_chance": 0},
                {"alternatives": [
                    {"prototype": "vine_strip", "count": 1, "destroy_chance": 0},
                    {"prototype": "vine", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 5),
            ("process_descs", [
                {"desc": "你开始制作椰壳水壶...", "repeat": 2},
                {"desc": "椰壳水壶制作完成！", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着用藤条封住椰壳的图案。"),
            ("desc_smell", "石片上残留着干草纤维碎屑，有一股干燥的草木气息。"),
        ],
    },
    {
        "prototype_key": "recipe_chopsticks",
        "prototype_parent": "recipe_base",
        "key": "筷子配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "用石刃将树枝或竹枝削成筷子"),
            ("background", "用石刃将树枝或竹枝削成筷子。"),
            ("output", "chopsticks"),
            ("build_location", "inventory"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "tree_branch", "count": 2, "destroy_chance": 0},
                    {"prototype": "bamboo_twig", "count": 2, "destroy_chance": 0},
                ]},
            ]),
            ("craft_tool", "cutting"),
            ("duration", 3),
            ("process_descs", [
                {"desc": "你用石刃削着木条...", "repeat": 2},
                {"desc": "筷子做好了！", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着两根细棍的图案。"),
            ("desc_smell", "石片上沾着椰壳纤维的碎屑，隐约能闻到一丝椰香。"),
        ],
    },
    {
        "prototype_key": "recipe_bamboo_straw",
        "prototype_parent": "recipe_base",
        "key": "吸管配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "用石刃将竹枝打通制成吸管"),
            ("background", "用石刃将竹枝打通，制成吸管。"),
            ("output", "bamboo_straw"),
            ("build_location", "inventory"),
            ("materials", [
                {"prototype": "bamboo_twig", "count": 1, "destroy_chance": 0},
            ]),
            ("craft_tool", "cutting"),
            ("duration", 2),
            ("process_descs", [
                {"desc": "你用石刃打通竹节...", "repeat": 1},
                {"desc": "吸管做好了！", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着一根中空竹管的图案。"),
            ("desc_smell", "石片上有新鲜的木屑碎片，散发着打磨过的木质清香。"),
        ],
    },
    {
        "prototype_key": "recipe_fish_trap",
        "prototype_parent": "recipe_base",
        "key": "捕鱼笼配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "make"),
            ("desc", "用藤条和木料编织捕鱼笼"),
            ("background", "用藤条和木料编织一个捕鱼笼。"),
            ("output", "fish_trap"),
            ("build_location", "inventory"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "vine_strip", "count": 5, "destroy_chance": 0},
                    {"prototype": "bamboo_twig", "count": 5, "destroy_chance": 0},
                    {"prototype": "wood_stick", "count": 5, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "vine", "count": 10, "destroy_chance": 0},
                    {"prototype": "vine_bark", "count": 10, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 10),
            ("process_descs", [
                {"desc": "你开始编织捕鱼笼...", "repeat": 3},
                {"desc": "捕鱼笼逐渐成形。", "repeat": 3},
                {"desc": "捕鱼笼编织完成！", "repeat": 1},
            ]),
            ("desc_look", "一块石片，刻着编织笼状结构的图案。"),
            ("desc_smell", "石片上有竹屑碎片，散发着淡淡的竹叶清香。"),
        ],
    },

    # ── 新增设施 ──
    {
        "prototype_key": "small_fire",
        "prototype_parent": "non_living",
        "typeclass": "survival.objects.Campfire",
        "key": "小型篝火",
        "locks": "get:false()",
        "attrs": [
            ("commands", [("ignite", "commands/ignite.py"), ("addfuel", "commands/addfuel.py"), ("extinguish", "commands/extinguish.py")], "system", ""),
            ("scripts", [("burn_timer", "scripts/burn_timer.py")], "system", ""),
            ("fire_state", "unlit"),
            ("burn_duration", 0),
            ("max_burn_duration", 600),
            ("desc_look", "几根木棍交叉搭成锥形，中间塞着干草和细枝，搭得整整齐齐。"),
            ("desc_burning", "木柴噼啪作响，火焰从柴堆缝隙间窜出，火光照亮了周围几步的范围。"),
            ("desc_extinguished", "柴堆已经塌陷，木炭冷却发白，灰烬被风吹得微微飘散，只剩下一堆黑灰色的残渣。"),
            ("desc_smell", "干燥的木柴散发着淡淡的木质气息。"),
            ("desc_smell_burning", "燃烧的篝火散发着呛人的烟熏味和焦木的辛香。"),
            ("desc_smell_extinguished", "熄灭的篝火残留着一股余烬的焦糊味和冷灰的苦涩气息。"),
        ],
    },
    {
        "prototype_key": "well",
        "prototype_parent": "non_living",
        "key": "水井",
        "locks": "get:false()",
        "attrs": [
            ("resource", [{"prototype": "fresh_water_item", "chance": 1.0}]),
            ("desc_look", "用石块垒成的一口浅井，井口约半臂宽，井壁石缝间渗出清澈的水珠，水面在井底微微晃动。"),
            ("desc_smell", "井口飘出湿润的泥土气息和清冽的水汽，带着地下泉水的甘甜。"),
            ("desc_taste", "井水清甜甘冽，没有异味。"),
        ],
    },
    {
        "prototype_key": "campfire",
        "prototype_parent": "non_living",
        "typeclass": "survival.objects.Campfire",
        "key": "营火",
        "locks": "get:false()",
        "attrs": [
            ("persistent", True),
            ("commands", [("ignite", "commands/ignite.py"), ("addfuel", "commands/addfuel.py"), ("extinguish", "commands/extinguish.py")], "system", ""),
            ("scripts", [("burn_timer", "scripts/burn_timer.py")], "system", ""),
            ("fire_state", "unlit"),
            ("burn_duration", 0),
            ("max_burn_duration", 600),
            ("desc_look", "石块围成一圈火塘，中间堆着木柴和引火物，搭得稳稳当当。"),
            ("desc_burning", "石圈内的火焰跳动着，火光映在石壁上，噼啪声不断。"),
            ("desc_burnt_out", "石圈内的木柴已经烧尽，只剩下一堆灰白色的余烬，偶尔冒出一缕青烟。石壁被烟熏得发黑。"),
            ("desc_smell", "干燥的木柴散发着淡淡的木质气息。"),
            ("desc_smell_burning", "燃烧的营火散发着呛人的烟熏味和焦木的辛香。"),
            ("desc_smell_burnt_out", "熄灭的火塘残留着一股余烬的焦糊味和冷灰的苦涩气息。"),
        ],
    },
    {
        "prototype_key": "tent",
        "prototype_parent": "non_living",
        "typeclass": "survival.objects.Tent",
        "key": "帐篷",
        "locks": "get:false()",
        "attrs": [
            ("commands", [("sleep", "commands/sleep.py")], "system", ""),
            ("stamina_bonus", 0.5),
            ("desc_look", "一顶用树叶和木棍搭建的简易帐篷。"),
            ("desc_smell", "帐篷内弥漫着干燥的树叶气息和木棍的清香，有一股温馨的庇护所味道。"),
        ],
    },
    {
        "prototype_key": "leaf_bed",
        "prototype_parent": "non_living",
        "key": "树叶床",
        "locks": "get:false()",
        "attrs": [
            ("stamina_bonus", 0.3),
            ("desc_look", "一张用棕榈叶铺成的简易床铺。"),
            ("desc_smell", "树叶床散发着棕榈叶特有的清新草香，铺得厚实的地方有一股温润的植物气息。"),
        ],
    },

    # ── 新增 build 类型配方（3 个）──
    {
        "prototype_key": "recipe_campfire",
        "prototype_parent": "recipe_base",
        "key": "篝火配方",
        "attrs": [
            ("recipe_type", "build"),
            ("desc", "用木棍和引火物搭建小型篝火"),
            ("background", "用木棍和引火物搭建一个小型篝火。"),
            ("output", "small_fire"),
            ("build_location", "room"),
            ("materials", [
                {"prototype": "wood_stick", "count": 2, "destroy_chance": 0},
                {"alternatives": [
                    {"prototype": "tree_branch", "count": 2, "destroy_chance": 0},
                    {"prototype": "bamboo_twig", "count": 2, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "dry_grass", "count": 1, "destroy_chance": 0},
                    {"prototype": "dry_moss", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 0),
            ("process_descs", []),
            ("requires", []),
            ("environment", None),
            ("desc_look", "一块石片，刻着木柴交叉搭成锥形的图案。"),
            ("desc_smell", "石片上缠着几根藤丝，有新鲜的藤条草木气息。"),
        ],
        "locks": "use:has_materials()",
    },
    {
        "prototype_key": "recipe_well",
        "prototype_parent": "recipe_base",
        "key": "水井配方",
        "attrs": [
            ("recipe_type", "build"),
            ("desc", "用石块垒砌水井，获取地下水"),
            ("background", "在地面挖一个浅坑，用石块垒砌井壁，藤条绑扎固定。"),
            ("output", "well"),
            ("build_location", "room"),
            ("materials", [
                {"prototype": "stone", "count": 4, "destroy_chance": 0},
                {"prototype": "wood_stick", "count": 1, "destroy_chance": 0},
                {"prototype": "vine_strip", "count": 2, "destroy_chance": 0},
            ]),
            ("duration", 5),
            ("process_descs", [
                {"desc": "你在地面上挖出一个浅坑，泥土松软，很快见水。", "repeat": 1},
                {"desc": "你把石块一块块垒起来，藤条缠紧固定。", "repeat": 3},
                {"desc": "井壁砌好了，井底渗出清澈的水。", "repeat": 1},
            ]),
            ("requires", []),
            ("environment", None),
            ("desc_look", "一块石片，刻着石块垒砌井壁的图案，旁边画着水波纹。"),
            ("desc_smell", "石片散发着干燥的矿物气息，刻痕处有淡淡的石粉味。"),
        ],
        "locks": "use:has_materials()",
    },
    {
        "prototype_key": "recipe_campfire_persistent",
        "prototype_parent": "recipe_base",
        "key": "营火配方",
        "attrs": [
            ("recipe_type", "build"),
            ("desc", "用石块围成火塘，搭建持久营火"),
            ("background", "用石块围成火塘，木柴架在中间，比普通篝火更耐久。"),
            ("output", "campfire"),
            ("build_location", "room"),
            ("materials", [
                {"prototype": "stone", "count": 3, "destroy_chance": 0},
                {"prototype": "wood_stick", "count": 2, "destroy_chance": 0},
                {"alternatives": [
                    {"prototype": "tree_branch", "count": 2, "destroy_chance": 0},
                    {"prototype": "bamboo_twig", "count": 2, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "dry_grass", "count": 1, "destroy_chance": 0},
                    {"prototype": "dry_moss", "count": 1, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 5),
            ("process_descs", [
                {"desc": "你选了一块平地，把石块摆成一圈。", "repeat": 1},
                {"desc": "你把木棍交叉搭在石圈里，塞入引火物。", "repeat": 2},
                {"desc": "石圈火塘搭好了，比普通篝火结实得多。", "repeat": 1},
            ]),
            ("requires", []),
            ("environment", None),
            ("desc_look", "一块石片，刻着石块围成火塘的图案，中间画着木柴交叉。"),
            ("desc_smell", "石片散发着干燥的矿物气息，刻痕处有淡淡的石粉味。"),
        ],
        "locks": "use:has_materials()",
    },
    {
        "prototype_key": "recipe_tent",
        "prototype_parent": "recipe_base",
        "key": "帐篷配方",
        "attrs": [
            ("recipe_type", "build"),
            ("desc", "用长棍和叶片搭建简易帐篷"),
            ("background", "用长棍和叶片搭建一个简易帐篷。"),
            ("output", "tent"),
            ("build_location", "room"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "long_stick", "count": 6, "destroy_chance": 0},
                    {"prototype": "long_bamboo_stick", "count": 6, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "palm_leaf", "count": 26, "destroy_chance": 0},
                    {"prototype": "banana_leaf", "count": 26, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "vine_strip", "count": 9, "destroy_chance": 0},
                    {"prototype": "vine_bark", "count": 9, "destroy_chance": 0},
                    {"prototype": "vine", "count": 9, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 0),
            ("process_descs", [
                # ── 选址 ──
                {"desc": "你选了一块平整的地面，开始规划帐篷的位置和朝向。", "repeat": 1},
                # ── 搭建框架：每插两根棍立即绑扎 ──
                {"group": [
                    {"desc": "你将一根长棍斜插进泥土里，用力夯实底部。", "repeat": 2},
                    {"desc": "你用藤条将两根棍子的交叉处牢牢绑紧，打了一个死结。", "repeat": 1},
                ], "repeat": 3},
                # ── 横梁 + 检查 ──
                {"desc": "你取来长棍横搭在骨架中间，用藤条固定住横梁。", "repeat": 1},
                {"desc": "框架逐渐成形，你逐个检查了连接点的牢固程度。", "repeat": 1},
                # ── 铺设叶片：每铺几片立即用藤条固定 ──
                {"group": [
                    {"desc": "你从底部往上铺设叶片，一片压一片，像鱼鳞一样层层叠叠。", "repeat": 4},
                    {"desc": "你用藤条穿过叶柄绑在骨架上，将叶片固定牢。", "repeat": 1},
                ], "repeat": 4},
                # ── 收口：向顶端合拢 + 固定 ──
                {"group": [
                    {"desc": "叶片从两侧向顶端逐渐合拢，你仔细调整每一片的搭接方向。", "repeat": 2},
                    {"desc": "你用藤条将叶片绑紧在顶端骨架上。", "repeat": 1},
                ], "repeat": 2},
                # ── 封顶 + 加固 + 完成 ──
                {"desc": "你将最后几片叶片覆盖在顶端，仔细调整了排水方向。", "repeat": 1},
                {"desc": "用藤条将顶部叶片收拢扎紧，防止雨水灌入。", "repeat": 1},
                {"desc": "你退后几步端详了一番，又回来加固了几个松动的绑扎点。", "repeat": 1},
                {"desc": "帐篷搭建完成，看起来结实又防雨。", "repeat": 1},
            ]),
            ("environment", None),
            ("desc_look", "一块石片，刻着用长棍和叶片搭建帐篷的图案。"),
            ("desc_smell", "石片上有烟熏的痕迹，闻起来有一股淡淡的焦木味。"),
        ],
        "locks": "use:has_materials()",
    },
    {
        "prototype_key": "recipe_leaf_bed",
        "prototype_parent": "recipe_base",
        "key": "树叶床配方",
        "attrs": [
            ("recipe_type", "build"),
            ("desc", "用树叶铺设简易床铺"),
            ("background", "用树叶铺设一张简易床铺，需要帐篷遮挡。"),
            ("output", "leaf_bed"),
            ("build_location", "container"),
            ("build_container", "tent"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "palm_leaf", "count": 5, "destroy_chance": 0},
                    {"prototype": "banana_leaf", "count": 5, "destroy_chance": 0},
                ]},
            ]),
            ("duration", 0),
            ("process_descs", [
                {"desc": "你走进帐篷，蹲下身子打量着地面……", "repeat": 1},
                {"desc": "你用手将地面上的碎石和枝条清理干净，拨出一小块平整的区域。", "repeat": 1},
                {"group": [
                    {"desc": "你拿起一片叶子，铺在地面上，仔细调整位置使其紧贴地面。", "repeat": 1},
                    {"desc": "你将叶子的边缘向内折入，压实边角。", "repeat": 1},
                    {"desc": "你用手掌将铺好的叶片按压平整，排出层间的空隙。", "repeat": 1},
                ], "repeat": 3},
                {"desc": "你把多余叶尖塞入边缘缝隙，让铺面更加紧密。", "repeat": 1},
                {"desc": "你站起来踩了踩，感觉软硬适中。", "repeat": 1},
                {"desc": "你在铺好的叶床侧面坐下，试了试弹性，点点头。", "repeat": 1},
            ]),
            ("requires", [
                {"type": "room_has", "prototype": "tent"},
                {"type": "room_not_has", "prototype": "leaf_bed"},
            ]),
            ("environment", None),
            ("desc_look", "一块石片，刻着叶片铺成床铺的图案。"),
            ("desc_smell", "石片上有新鲜的叶片碎屑，散发着干燥的草木气息。"),
        ],
        "locks": "use:has_materials()",
    },

    # ── 新增 cook 类型配方（1 个）──
    {
        "prototype_key": "recipe_roast_meat",
        "prototype_parent": "recipe_base",
        "key": "烤肉配方",
        "attrs": [
            ("recipe_type", "cook"),
            ("desc", "用签子串起生肉在火上烤制"),
            ("background", "用签子串起生肉在火上烤制。"),
            ("output", "cooked_meat"),
            ("build_location", "inventory"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "raw_meat", "count": 1, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "tree_branch", "count": 1, "destroy_chance": 1},
                    {"prototype": "bamboo_twig", "count": 1, "destroy_chance": 1},
                ]},
            ]),
            ("duration", 20),
            ("process_descs", [
                {"desc": "你将肉串在签子上，架在火上烤...", "repeat": 2},
                {"desc": "肉香四溢。", "repeat": 2},
                {"desc": "烤肉完成了！", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 20}),
            ("requires", []),
            ("desc_look", "一块石片，刻着肉串在签子上架于火上的图案。"),
            ("desc_smell", "石片上有棕榈叶的碎纤维，有一股淡淡的干草气息。"),
        ],
        "locks": "use:has_materials()",
    },

    # ── 新增食物原型（烤肉配方的材料/产出依赖）──
    {
        "prototype_key": "raw_meat",
        "prototype_parent": "animalpart_meat",
        "key": "生肉",
        "attrs": [
            ("item_type", "solid"),
            ("can_eat", False),
            ("desc_look", "一块暗红色的生肉，表面带着血丝，肉质松软，散发着淡淡的腥味。"),
            ("desc_smell", "生肉散发着一股浓重的血腥气，混着淡淡的铁锈味，令人本能地皱起鼻子。"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "cooked_meat",
        "prototype_parent": "animalpart_meat",
        "key": "熟肉",
        "attrs": [
            ("can_eat", True), ("hunger_value", 25),
            ("desc_look", "一块烤得恰到好处的肉，散发着诱人的香气。"),
            ("desc_smell", "烤肉散发着浓郁的焦香，油脂滴落产生的烟雾带着令人垂涎的肉香。"),
        ],
    },

    # ── LC-01d 烹饪系统闭环新增 prototype ──

    # ── 煮水配方 ──
    {
        "prototype_key": "recipe_boilwater",
        "prototype_parent": "recipe_base",
        "key": "沸水配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("commands", [("cook", "commands/cook.py")], "system", ""),
            ("recipe_type", "cook"),
            ("desc", "将水煮沸得到热水"),
            ("background", "用火将水煮沸。"),
            ("output", "hot_water_item"),
            ("build_location", "vessel_content"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "dirty_water_item", "count": 1, "in_container": True},
                    {"prototype": "fresh_water_item", "count": 1, "in_container": True},
                ]},
            ]),
            ("duration", 30),
            ("process_descs", [
                {"desc": "你将容器放在火上，开始烧水...", "repeat": 2},
                {"desc": "水沸腾了。", "repeat": 1},
                {"desc": "水烧开了，冒着热气。", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 30}),
            ("requires", []),
            ("desc_look", "一块石片，刻着将容器放在火上烧水的图案。"),
            ("desc_smell", "石片上残留着油脂的气味，是之前参照烤肉时沾上的。"),
        ],
    },

    # ── 煮盐配方 ──
    {
        "prototype_key": "recipe_boilsalt",
        "prototype_parent": "recipe_base",
        "key": "煮盐配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("commands", [("cook", "commands/cook.py")], "system", ""),
            ("recipe_type", "cook"),
            ("desc", "将海水倒入椰壳中煮干得到盐"),
            ("background", "将咸水煮干，留下白色的盐粒。"),
            ("output", "salt"),
            ("build_location", "inventory"),
            ("materials", [
                # 海水：原料，消耗
                {"prototype": "salt_water_item", "count": 1,
                 "destroy_chance": 1, "search_scope": "room_contents"},
                # 椰壳：烹饪工具，不消耗（椰壳水壶排除）
                {"prototype": "coconut_shell", "count": 1,
                 "destroy_chance": 0, "search_scope": "room"},
            ]),
            ("duration", 30),
            ("process_descs", [
                {"desc": "你将海水倒入椰壳，放在火上...", "repeat": 1},
                {"desc": "咸水慢慢蒸发...", "repeat": 2},
                {"desc": "水份蒸干，留下了白色的盐。", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 30}),
            ("requires", []),
            ("desc_look", "一块石片，刻着椰壳中水分蒸发留下白粒的图案。"),
            ("desc_smell", "石片边缘有一圈水渍的痕迹，闻起来有一股淡淡的矿物质气息。"),
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # LC-04 捕鱼闭环新增 prototype
    # ══════════════════════════════════════════════════════════════════════

    # ── 水产（LC-04 §1.2） ──

    # 红树林水产（5 种）
    {
        "prototype_key": "mudskipper",
        "prototype_parent": ("animalia_actinopterygii", "animalpart_meat"),
        "key": "弹涂鱼",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一条手掌大小的弹涂鱼，还在蹦跳。"),
            ("desc_smell", "弹涂鱼散发着泥腥味和淡淡的海水咸味。"),
            ("dishes_name", "弹涂鱼"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "mangrove_shrimp",
        "prototype_parent": ("animalia_decapoda", "animalpart_meat"),
        "key": "近缘新对虾",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "几只半透明的虾，触须还在微微摆动。"),
            ("desc_smell", "对虾散发着淡淡的海水腥味，虾壳处有一股鲜甜的气息。"),
            ("dishes_name", "近缘新对虾"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "mud_crab",
        "prototype_parent": ("animalia_brachyura", "animalpart_meat"),
        "key": "锯缘青蟹",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一只青壳螃蟹，螯钳有力地挥舞着。"),
            ("desc_smell", "青蟹散发着咸湿的泥腥味，螯钳处隐约有股水草的气息。"),
            ("dishes_name", "锯缘青蟹"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "mangrove_clam",
        "prototype_parent": ("animalia_mollusca_bivalvia", "animalpart_meat"),
        "key": "红树蚬",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "几枚灰褐色的蚬壳，尚紧闭着。"),
            ("desc_smell", "红树蚬散发着淤泥和海水混合的腥咸气息。"),
            ("dishes_name", "红树蚬"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "sea_slug",
        "prototype_parent": ("animalia_mollusca_gastropoda", "animalpart_meat"),
        "key": "石磺",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一块软绵绵的海洋生物，外形像无壳的蜗牛。"),
            ("desc_smell", "石磺散发着浓烈的海腥味，黏液处有一股奇异的碘味。"),
            ("dishes_name", "石磺"),
            ("hunger_restore", 0),
        ],
    },

    # 海蚀洞水产（5 种）
    {
        "prototype_key": "grouper",
        "prototype_parent": ("animalia_actinopterygii", "animalpart_meat"),
        "key": "石斑鱼",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一条花纹斑斓的石斑鱼，肉质看起来很结实。"),
            ("desc_smell", "石斑鱼散发着海水的咸腥味，鱼肉处隐约有一股鲜甜的气息。"),
            ("dishes_name", "石斑鱼"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "spiny_lobster",
        "prototype_parent": ("animalia_decapoda", "animalpart_meat"),
        "key": "龙虾",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一只浑身长刺的龙虾，体型不大但甲壳坚硬。"),
            ("desc_smell", "龙虾散发着海水的咸味，甲壳处有一股淡淡的矿物质的气息。"),
            ("dishes_name", "龙虾"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "reef_crab",
        "prototype_parent": ("animalia_brachyura", "animalpart_meat"),
        "key": "面包蟹",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一只圆滚滚的面包蟹，背壳像个小面包。"),
            ("desc_smell", "面包蟹散发着岩礁海水的咸腥味，蟹壳缝隙间有淡淡的海藻气息。"),
            ("dishes_name", "面包蟹"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "oyster",
        "prototype_parent": ("animalia_mollusca_bivalvia", "animalpart_meat"),
        "key": "牡蛎",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一枚粗糙的牡蛎壳，里面隐约可见白嫩的肉。"),
            ("desc_smell", "牡蛎散发着浓郁的海水咸味和矿物质气息，壳内隐约飘出鲜甜的海味。"),
            ("dishes_name", "牡蛎"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "sea_snail",
        "prototype_parent": ("animalia_mollusca_gastropoda", "animalpart_meat"),
        "key": "棘螺",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一个布满棘刺的海螺壳，沉甸甸的。"),
            ("desc_smell", "海螺散发着咸腥的海水味，螺口处有一股浓重的海洋气息。"),
            ("dishes_name", "棘螺"),
            ("hunger_restore", 0),
        ],
    },

    # 淡水湖水产（5 种）
    {
        "prototype_key": "tilapia",
        "prototype_parent": ("animalia_actinopterygii", "animalpart_meat"),
        "key": "罗非鱼",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一条银灰色的罗非鱼，鳞片在光线下闪亮。"),
            ("desc_smell", "罗非鱼散发着淡水鱼特有的土腥味，鱼鳃处腥气略重。"),
            ("dishes_name", "罗非鱼"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "river_shrimp",
        "prototype_parent": ("animalia_decapoda", "animalpart_meat"),
        "key": "日本沼虾",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一只透明的淡水虾，长须细足还在水中划动。"),
            ("desc_smell", "淡水虾散发着淡淡的清水气息和微弱的虾腥味。"),
            ("dishes_name", "日本沼虾"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "stream_crab",
        "prototype_parent": ("animalia_brachyura", "animalpart_meat"),
        "key": "中华溪蟹",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一只小巧的溪蟹，壳呈深褐色，行动敏捷。"),
            ("desc_smell", "溪蟹散发着溪水般清冽的泥土气息，蟹壳上带着淡淡的水草味道。"),
            ("dishes_name", "中华溪蟹"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "freshwater_mussel",
        "prototype_parent": ("animalia_mollusca_bivalvia", "animalpart_meat"),
        "key": "河蚌",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一枚椭圆形的河蚌，外壳墨绿，微微张开。"),
            ("desc_smell", "河蚌散发着湖底淤泥的土腥味，蚌壳微张处冒出一丝清水的气息。"),
            ("dishes_name", "河蚌"),
            ("hunger_restore", 0),
        ],
    },
    {
        "prototype_key": "pond_snail",
        "prototype_parent": ("animalia_mollusca_gastropoda", "animalpart_meat"),
        "key": "田螺",
        "attrs": [
            ("can_eat", False),
            ("item_type", "solid"),
            ("desc_look", "一个圆锥形的田螺，壳上有螺旋纹路。"),
            ("desc_smell", "田螺散发着泥土和水草混合的清新气息，螺壳上有一股淡淡的淤泥味道。"),
            ("dishes_name", "田螺"),
            ("hunger_restore", 0),
        ],
    },

    # ── 水域对象（LC-04 §1.3） ──
    {
        "prototype_key": "mangrove_water",
        "prototype_parent": "non_living",
        "key": "红树林水道",
        "locks": "get:false()",
        "attrs": [
            ("resource", []),
            ("fish_resource", [
                {"prototype": "mudskipper", "chance": 0.4},
                {"prototype": "mangrove_shrimp", "chance": 0.35},
                {"prototype": "mud_crab", "chance": 0.25},
                {"prototype": "mangrove_clam", "chance": 0.3},
                {"prototype": "sea_slug", "chance": 0.2},
            ]),
            ("desc_look", "红树林根系交错的水道，水下似有生物活动的迹象。"),
            ("desc_smell", "红树林水道弥漫着咸湿的海水味和红树根系特有的腐殖气息，闷热而潮腥。"),
        ],
    },
    {
        "prototype_key": "cave_pool",
        "prototype_parent": "non_living",
        "key": "海蚀洞水潭",
        "locks": "get:false()",
        "attrs": [
            ("resource", []),
            ("fish_resource", [
                {"prototype": "grouper", "chance": 0.3},
                {"prototype": "spiny_lobster", "chance": 0.15},
                {"prototype": "reef_crab", "chance": 0.25},
                {"prototype": "oyster", "chance": 0.35},
                {"prototype": "sea_snail", "chance": 0.3},
            ]),
            ("desc_look", "幽暗的海蚀洞水潭，水波不兴，偶有气泡上浮。"),
            ("desc_smell", "海蚀洞水潭散发着冰冷的石灰岩矿物气息，潮湿的空气中弥漫着隐约的海腥味。"),
        ],
    },
    {
        "prototype_key": "freshwater_lake",
        "prototype_parent": "non_living",
        "key": "清澈的湖泊",
        "locks": "get:false()",
        "attrs": [
            ("resource", []),
            ("desc_look", "碧绿的湖水清澈见底，水下有鱼影闪动。"),
            ("desc_smell", "清澈的湖水散发着清新的水汽，夹杂着水草和湿润泥土的淡雅气息。"),
        ],
    },

    # ── 水产加工产出物（LC-04 §1.4） ──
    {
        "prototype_key": "roasted_aquatic",
        "prototype_parent": "animalpart_meat",
        "key": "烤水产",
        "attrs": [
            ("can_eat", True),
            ("hunger_restore", 15),
            ("desc_look", "一份烤制的水产，散发着诱人的香气。"),
            ("desc_smell", "烤水产散发着焦香的烤肉气息，夹杂着海水的鲜味和木炭的烟熏味。"),
        ],
    },
    {
        "prototype_key": "salted_roasted_aquatic",
        "prototype_parent": "animalpart_meat",
        "key": "鲜美的烤水产",
        "attrs": [
            ("can_eat", True),
            ("hunger_restore", 20),
            ("stamina_restore", 10),
            ("desc_look", "一份加了盐的烤水产，咸香可口。"),
            ("desc_smell", "盐烤水产散发着浓郁的咸香，焦脆的外皮处飘着令人垂涎的烟熏和海鲜混合香气。"),
        ],
    },
    {
        "prototype_key": "aquatic_soup",
        "prototype_parent": "animalpart_meat",
        "key": "水产汤",
        "attrs": [
            ("commands", [("drink", "commands/drink.py"), ("eat", "commands/eat.py"), ("empty", "commands/empty.py")], "system", ""),
            ("can_drink", True), ("can_eat", True),
            ("thirst_restore", 15), ("hunger_restore", 12),
            ("embedded_vessel", "coconut_shell"),
            ("drink_consumed", False), ("eat_consumed", False),
            ("desc_look", "一碗热腾腾的水产汤，汤色乳白。"),
            ("desc_smell", "水产汤散发着浓郁的热气和鲜味，乳白色的汤汁飘着淡淡的椰香和海鲜的鲜甜。"),
        ],
    },
    {
        "prototype_key": "salted_aquatic_soup",
        "prototype_parent": "animalpart_meat",
        "key": "鲜美的水产汤",
        "attrs": [
            ("commands", [("drink", "commands/drink.py"), ("eat", "commands/eat.py"), ("empty", "commands/empty.py")], "system", ""),
            ("can_drink", True), ("can_eat", True),
            ("hunger_restore", 18),
            ("thirst_restore", 20),
            ("stamina_restore", 8),
            ("embedded_vessel", "coconut_shell"),
            ("drink_consumed", False), ("eat_consumed", False),
            ("desc_look", "一碗鲜美的水产汤，咸鲜醇厚。"),
            ("desc_smell", "鲜美的水产汤散发着浓郁的咸鲜香气，盐和海鲜的味道交织在一起，热气扑鼻。"),
        ],
    },

    # ── 水产 cook 配方（LC-04 §1.8） ──

    # 烤水产配方（无盐，动态产出）
    {
        "prototype_key": "recipe_roast_aquatic",
        "prototype_parent": "recipe_base",
        "key": "烤水产配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "cook"),
            ("desc", "用签子串起水产在火上烤制"),
            ("background", "用签子串起水产在火上烤制。"),
            ("output", "roasted_aquatic"),
            ("build_location", "inventory"),
            ("dynamic_output", True),
            ("output_template", "烤{dishes_name}"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "mudskipper", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "mud_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_clam", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_slug", "count": 1, "destroy_chance": 0},
                    {"prototype": "grouper", "count": 1, "destroy_chance": 0},
                    {"prototype": "spiny_lobster", "count": 1, "destroy_chance": 0},
                    {"prototype": "reef_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "oyster", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_snail", "count": 1, "destroy_chance": 0},
                    {"prototype": "tilapia", "count": 1, "destroy_chance": 0},
                    {"prototype": "river_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "stream_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "freshwater_mussel", "count": 1, "destroy_chance": 0},
                    {"prototype": "pond_snail", "count": 1, "destroy_chance": 0},
                ]},
                {"alternatives": [
                    {"prototype": "tree_branch", "count": 1, "destroy_chance": 1},
                    {"prototype": "bamboo_twig", "count": 1, "destroy_chance": 1},
                ]},
            ]),
            ("duration", 15),
            ("process_descs", [
                {"desc": "你将水产串在签子上，架在火上烤...", "repeat": 2},
                {"desc": "烤制的香气渐渐飘散开来。", "repeat": 2},
                {"desc": "烤水产完成了！", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 15}),
            ("requires", []),
            ("desc_look", "一块石片，刻着水产串在签子上烤制的图案。"),
            ("desc_smell", "石片上有盐粒和鱼腥混合的气味，还有一丝椰壳的清甜。"),
        ],
    },

    # ── v7 动态配方模板（LC-01d） ──

    # 加盐烤水产配方（动态）
    {
        "prototype_key": "recipe_tasty_roast_aquatic",
        "prototype_parent": "recipe_base",
        "key": "鲜美的烤水产配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "cook"),
            ("desc", "用签子和盐烤制调味水产"),
            ("background", "用签子串起水产，撒上盐，在火上精心烤制。"),
            ("output", "salted_roasted_aquatic"),
            ("build_location", "inventory"),
            ("dynamic_output", True),
            ("output_template", "鲜美的烤{dishes_name}"),
            ("output_base", "salted_roasted_aquatic"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "mudskipper", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "mud_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_clam", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_slug", "count": 1, "destroy_chance": 0},
                    {"prototype": "grouper", "count": 1, "destroy_chance": 0},
                    {"prototype": "spiny_lobster", "count": 1, "destroy_chance": 0},
                    {"prototype": "reef_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "oyster", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_snail", "count": 1, "destroy_chance": 0},
                    {"prototype": "tilapia", "count": 1, "destroy_chance": 0},
                    {"prototype": "river_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "stream_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "freshwater_mussel", "count": 1, "destroy_chance": 0},
                    {"prototype": "pond_snail", "count": 1, "destroy_chance": 0},
                ]},
                {"prototype": "salt", "count": 1, "destroy_chance": 1},
                {"alternatives": [
                    {"prototype": "tree_branch", "count": 1, "destroy_chance": 1},
                    {"prototype": "bamboo_twig", "count": 1, "destroy_chance": 1},
                ]},
            ]),
            ("duration", 20),
            ("process_descs", [
                {"desc": "你将水产串在签子上，撒上盐...", "repeat": 1},
                {"desc": "水产在火上滋滋作响，咸香飘散。", "repeat": 2},
                {"desc": "香气四溢，烤水产完成了！", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 20}),
            ("requires", []),
            ("desc_look", "一块石片，刻着水产串在签子上、旁边撒着颗粒的图案。"),
            ("desc_smell", "石片散发干燥的矿物气息，刻痕处有淡淡的石粉味。"),
        ],
    },

    # 水产汤配方（动态）
    {
        "prototype_key": "recipe_aquatic_soup",
        "prototype_parent": "recipe_base",
        "key": "水产汤配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "cook"),
            ("desc", "用椰壳煮水产汤"),
            ("background", "将水产和椰壳一起煮成鲜美的汤。"),
            ("output", "aquatic_soup"),
            ("build_location", "inventory"),
            ("dynamic_output", True),
            ("output_template", "{dishes_name}汤"),
            ("output_base", "aquatic_soup"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "mudskipper", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "mud_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_clam", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_slug", "count": 1, "destroy_chance": 0},
                    {"prototype": "grouper", "count": 1, "destroy_chance": 0},
                    {"prototype": "spiny_lobster", "count": 1, "destroy_chance": 0},
                    {"prototype": "reef_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "oyster", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_snail", "count": 1, "destroy_chance": 0},
                    {"prototype": "tilapia", "count": 1, "destroy_chance": 0},
                    {"prototype": "river_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "stream_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "freshwater_mussel", "count": 1, "destroy_chance": 0},
                    {"prototype": "pond_snail", "count": 1, "destroy_chance": 0},
                ]},
                {"prototype": "coconut_shell", "count": 1, "destroy_chance": 1},
            ]),
            ("duration", 25),
            ("process_descs", [
                {"desc": "你将水产放入椰壳中，加水上火煮...", "repeat": 1},
                {"desc": "汤咕嘟咕嘟地冒着泡。", "repeat": 2},
                {"desc": "一锅鲜美的汤做好了！", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 25}),
            ("requires", []),
            ("desc_look", "一块石片，刻着椰壳盛汤的图案。"),
            ("desc_smell", "石片散发干燥的矿物气息，刻痕处有淡淡的石粉味。"),
        ],
    },

    # 鲜美的水产汤配方（动态）
    {
        "prototype_key": "recipe_tasty_aquatic_soup",
        "prototype_parent": "recipe_base",
        "key": "鲜美的水产汤配方",
        "locks": "use:has_materials()",
        "attrs": [
            ("recipe_type", "cook"),
            ("desc", "用椰壳和盐煮调味水产汤"),
            ("background", "将水产、盐和椰壳一起煮成浓郁鲜美的汤。"),
            ("output", "salted_aquatic_soup"),
            ("build_location", "inventory"),
            ("dynamic_output", True),
            ("output_template", "鲜美的{dishes_name}汤"),
            ("output_base", "salted_aquatic_soup"),
            ("materials", [
                {"alternatives": [
                    {"prototype": "mudskipper", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "mud_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "mangrove_clam", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_slug", "count": 1, "destroy_chance": 0},
                    {"prototype": "grouper", "count": 1, "destroy_chance": 0},
                    {"prototype": "spiny_lobster", "count": 1, "destroy_chance": 0},
                    {"prototype": "reef_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "oyster", "count": 1, "destroy_chance": 0},
                    {"prototype": "sea_snail", "count": 1, "destroy_chance": 0},
                    {"prototype": "tilapia", "count": 1, "destroy_chance": 0},
                    {"prototype": "river_shrimp", "count": 1, "destroy_chance": 0},
                    {"prototype": "stream_crab", "count": 1, "destroy_chance": 0},
                    {"prototype": "freshwater_mussel", "count": 1, "destroy_chance": 0},
                    {"prototype": "pond_snail", "count": 1, "destroy_chance": 0},
                ]},
                {"prototype": "salt", "count": 1, "destroy_chance": 1},
                {"prototype": "coconut_shell", "count": 1, "destroy_chance": 1},
            ]),
            ("duration", 25),
            ("process_descs", [
                {"desc": "你将水产和盐放入椰壳中，加水上火煮...", "repeat": 1},
                {"desc": "汤咕嘟咕嘟地冒着泡，香气浓郁。", "repeat": 2},
                {"desc": "一锅浓郁的汤做好了！", "repeat": 1},
            ]),
            ("environment", {"fire": "burning", "burn_cost": 25}),
            ("requires", []),
            ("desc_look", "一块石片，刻着椰壳盛汤、旁边有白色颗粒的图案。"),
            ("desc_smell", "石片散发干燥的矿物气息，刻痕处有淡淡的石粉味。"),
        ],
    },
]

# ── 磨损态映射表（正常态 → 磨损态复合 prototype）──
WEAR_MAP = {
    "stone_blade": "worn_stone_blade",
    "stone_axe": "worn_stone_axe",
    "obsidian_axe": "worn_obsidian_axe",
}
