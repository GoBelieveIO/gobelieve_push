# -*- coding: utf-8 -*-
class WX(object):
    #保存公众号的access_token
    @classmethod
    def set_access_token(cls, rds, wx_appid, access_token, expires):
        key = "wx_token_%s"%wx_appid
        rds.set(key, access_token)
        rds.expire(key, expires)
    
    @classmethod
    def get_access_token(cls, rds, wx_appid):
        key = "wx_token_%s"%wx_appid
        return rds.get(key)

    @classmethod
    def set_componet_access_token(cls, rds, access_token, expires):
        key = "component_access_token"
        rds.set(key, access_token)
        rds.expire(key, expires)

    @classmethod
    def get_component_access_token(cls, rds):
        key = "component_access_token"
        return rds.get(key)

    @classmethod
    def set_pre_auth_code(cls, rds, pre_auth_code, expires):
        key = "component_pre_auth_code"
        rds.set(key, pre_auth_code)
        rds.expire(key, expires)

    @classmethod
    def get_pre_auth_code(cls, rds):
        key = "component_pre_auth_code"
        return rds.get(key)

    @classmethod
    def set_ticket(cls, rds, ticket):
        key = "component_ticket"
        rds.set(key, ticket)

    @classmethod
    def get_ticket(cls, rds):
        key = "component_ticket"
        return rds.get(key)
