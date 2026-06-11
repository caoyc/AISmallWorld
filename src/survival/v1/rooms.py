"""
房间类型类 - 支持五感描述
"""

from evennia.objects.objects import DefaultRoom


class SurvivalRoom(DefaultRoom):
    """支持五感描述的房间类型类。

    重写 get_display_desc() 以支持 desc_look 属性，
    提供 get_sense_description() 统一接口供感官指令调用。

    Attributes:
        db.desc (str): 通用描述，作为 desc_look 的回退。
        db.desc_look (str): 视觉描述（look 时展示）。
        db.desc_listen (str): 听觉描述（listen 时展示）。
        db.desc_smell (str): 嗅觉描述（smell 时展示）。
        db.desc_touch (str): 触觉描述（touch 时展示）。
        db.desc_taste (str): 味觉描述（taste 无目标时展示）。
    """

    DEFAULT_SENSE_MESSAGES = {
        "listen": "这里安安静静的，没有什么特别的声音。",
        "smell": "这里的空气没有什么特别的气味。",
        "touch": "你感受了一下周围，没有什么特别的触感。",
        "taste": "空气中没有什么可以品尝的味道。",
    }

    def get_display_desc(self, looker, **kwargs):
        """返回视觉描述，优先使用 desc_look。

        回退链：desc_look → desc → default_description

        Args:
            looker: 观察者（角色对象）。
            **kwargs: Evennia 传递的额外参数。

        Returns:
            str: 房间的视觉描述文本。
        """
        return self.db.desc_look or self.db.desc or self.default_description

    def get_sense_description(self, sense):
        """返回指定感官的描述文本。

        读取 desc_{sense} 属性，无值时返回默认消息。

        Args:
            sense (str): 感官类型，"look"/"listen"/"smell"/"touch"/"taste"。

        Returns:
            str: 感官描述文本。
        """
        desc = self.attributes.get(f"desc_{sense}")
        if desc:
            return desc
        if sense == "look":
            return self.db.desc or self.default_description
        return self.DEFAULT_SENSE_MESSAGES.get(sense, "你什么也没有感受到。")