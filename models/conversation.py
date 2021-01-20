# -*- coding: utf-8 -*-

class Conversation(object):
    @classmethod
    def do_not_disturb_key(cls, appid, uid):
        return "conversations_donotdisturb_%d_%d" % (appid, uid)

    @classmethod
    def get_do_not_disturb(cls, rds, appid, uid, peer_id=None, group_id=None):
        assert(peer_id or group_id)
        key = cls.do_not_disturb_key(appid, uid)
        if peer_id:
            member = "p:%s"%peer_id
        elif group_id:
            member = "g:%s"%group_id
        is_member = rds.sismember(key, member)
        return 1 if is_member else 0
