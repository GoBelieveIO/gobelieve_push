
# -*- coding: utf-8 -*-
import logging
import sys
import traceback

def get_app_name(mysql, appid):
    for i in range(2):
        try:
            sql = "select name from app where id=%s"
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            return obj["name"]
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue
    return ""

def get_p12(mysql, sandbox, appid):
    for i in range(2):
        try:
            sql = '''select sandbox_key, sandbox_key_secret, sandbox_key_utime,
                      production_key, production_key_secret, production_key_utime
                      from client_apns, client where client.app_id=%s and client.id=client_apns.client_id'''
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            if sandbox:
                p12 = obj["sandbox_key"]
                secret = obj["sandbox_key_secret"]
                timestamp = obj["sandbox_key_utime"]
            else:
                p12 = obj["production_key"]
                secret = obj["production_key_secret"]
                timestamp = obj["production_key_utime"]

            return p12, secret, timestamp
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            logging.info("exception:%s", str(e))
            continue

    return None, None, None

def get_certificate(mysql, appid):
    for i in range(2):
        try:
            sql = '''select cc.cer as cer, cc.pkey as pkey
                      from app, client as c, client_certificate as cc where c.app_id=%s and c.id=cc.client_id'''
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            cer = obj["cer"]
            key = obj["pkey"]
            return cer, key
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue

    return None, None


def get_xg_secret(mysql, appid):
    for i in range(2):
        try:
            sql = '''select cc.xinge_access_id as access_id, cc.xinge_secret_key as secret_key
                      from client as c, client_certificate as cc where c.app_id=%s and c.id=cc.client_id'''
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            access_id = obj["access_id"]
            secret_key = obj["secret_key"]
            return access_id, secret_key
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue

    return None, None


def get_mi_key(mysql, appid):
    for i in range(2):
        try:
            sql = '''select cc.mi_appid as appid, cc.mi_secret_key as app_secret
                      from client as c, client_certificate as cc where c.app_id=%s and c.id=cc.client_id'''
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            mi_appid = obj["appid"]
            mi_app_secret = obj["app_secret"]
            return mi_appid, mi_app_secret
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue

    return None, None




def get_hw_key(mysql, appid):
    for i in range(2):
        try:
            sql = '''select cc.hw_appid as appid, cc.hw_secret_key as app_secret
                      from client as c, client_certificate as cc where c.app_id=%s and c.id=cc.client_id'''
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            hw_appid = obj["appid"]
            hw_app_secret = obj["app_secret"]
            return hw_appid, hw_app_secret
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue

    return None, None



def get_gcm_key(mysql, appid):
    for i in range(2):
        try:
            sql = '''select cc.gcm_sender_id as sender_id, cc.gcm_api_key as api_key
                      from client as c, client_certificate as cc where c.app_id=%s and c.id=cc.client_id'''
            cursor = mysql.execute(sql, appid)
            obj = cursor.fetchone()
            sender_id = obj["sender_id"]
            api_key = obj["api_key"]
            return sender_id, api_key
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue

    return None, None

#获取微信公众号id
def get_wx(db, appid):
    for i in range(2):
        try:
            sql = "SELECT wx.gh_id as gh_id, wx.wx_app_id as wx_app_id, wx.refresh_token as refresh_token, app.store_id as store_id FROM app, client, client_wx as wx where app.id=%s and client.id=wx.client_id and app.id=client.app_id"
            r = db.execute(sql, appid)
            obj = r.fetchone()
            return obj
        except Exception, e:
            logging.info("exception:%s", str(e))
            continue

    return None
