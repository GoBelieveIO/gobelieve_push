
class User:
    def __init__(self):
        self.apns_device_token = None
        self.ng_device_token = None
        self.uid = None
        self.appid = None
        self.name = ""

def get_user(rds, appid, uid):
    u = User()
    key = "users_%s_%s"%(appid, uid)
    u.name, unread,\
    u.apns_device_token, apns_ts,\
    u.ng_device_token, ng_ts,\
    u.xg_device_token, xg_ts,\
    u.mi_device_token, mi_ts,\
    u.hw_device_token, hw_ts,\
    u.gcm_device_token, gcm_ts,\
    u.ali_device_token, ali_ts,\
    u.jp_device_token, jp_ts,\
    u.pushkit_device_token, pushkit_ts,\
    u.wx_openid, wx_ts = \
        rds.hmget(key, "name", "unread",
                  "apns_device_token", "apns_timestamp",
                  "ng_device_token",  "ng_timestamp",
                  "xg_device_token", "xg_timestamp",
                  "xm_device_token",  "xm_timestamp",
                  "hw_device_token", "hw_timestamp",
                  "gcm_device_token", "gcm_timestamp",
                  "ali_device_token", "ali_timestamp",
                  "jp_device_token", "jp_timestamp",
                  "pushkit_device_token", "pushkit_timestamp",
                  "wx_openid", "wx_timestamp")

    u.appid = appid
    u.uid = uid
    u.unread = int(unread) if unread else 0
    u.apns_timestamp = int(apns_ts) if apns_ts else 0
    u.ng_timestamp = int(ng_ts) if ng_ts else 0
    u.xg_timestamp = int(xg_ts) if xg_ts else 0
    u.mi_timestamp = int(mi_ts) if mi_ts else 0
    u.hw_timestamp = int(hw_ts) if hw_ts else 0
    u.gcm_timestamp = int(gcm_ts) if gcm_ts else 0
    u.ali_timestamp = int(ali_ts) if ali_ts else 0
    u.jp_timestamp = int(jp_ts) if jp_ts else 0
    u.pushkit_timestamp = int(pushkit_ts) if pushkit_ts else 0
    u.wx_timestamp = int(wx_ts) if wx_ts else 0    
    return u

def set_user_unread(rds, appid, uid, unread):
    key = "users_%s_%s"%(appid, uid)
    rds.hset(key, "unread", unread)

def get_user_name(rds, appid, uid):
    key = "users_%s_%s"%(appid, uid)
    return rds.hget(key, "name")

def get_user_notification_setting(rds, appid, uid, group_id):
    key = "users_%s_%s"%(appid, uid)
    quiet = rds.hget(key, "group_%d"%group_id)
    quiet = int(quiet) if quiet else 0
    return quiet

def get_user_do_not_disturb(rds, appid, uid, peer_uid):
    key = "users_%s_%s"%(appid, uid)
    q = rds.hget(key, "peer_%d"%peer_uid)
    return int(q) if q else 0
