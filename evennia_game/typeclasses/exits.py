"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        """出口遍历前检查：打断休息状态。"""
        if traversing_object.attributes.get("resting"):
            # 结算恢复值
            if hasattr(traversing_object, '_settle_recovery'):
                traversing_object._settle_recovery()
            traversing_object.db.resting = False
            traversing_object.db.rest_start_time = None
            traversing_object.db.rest_bonus = 0.0
            traversing_object.db.rest_last_settle = None
            traversing_object.msg("你结束了休息。")
            # 显示当前耐力
            stamina = traversing_object.db.stamina
            if hasattr(traversing_object, '_get_stamina_label'):
                label = traversing_object._get_stamina_label()
                traversing_object.msg(f"你的耐力：{stamina} [{label}]")

        super().at_traverse(traversing_object, target_location, **kwargs)
