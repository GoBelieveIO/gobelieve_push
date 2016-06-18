# -*- coding: utf-8 -*-
import time
import requests
import pickle
import json
import logging

from utils.func import random_ascii_string

import config
if config.DEBUG:
    from utils.wx import WX2 as WX
    from utils.wx_api import WXAPI2 as WXAPI
else:
    from utils.wx import WX
    from utils.wx_api import WXAPI
    
from models.wx import WX as weixin
from models import application

#平台appid
#平台appsecret
WX_APPID = config.WX_APPID
WX_APPSECRET = config.WX_APPSECRET


def _check_error(result):
    if result and result.get('errcode') > 0:
        logging.error("errmsg:%s", result.get('errmsg') or '公众号发送消息未知异常')
    return result

    
class WXPush(object):
    mysql = None
    rds = None
    apps = {}
    
    @staticmethod
    def get_component_access_token(rds):
        WX = weixin
        component_token = WX.get_component_access_token(rds)
        if not component_token:
            ticket = WX.get_ticket(rds)
            if not ticket:
                return None
     
            wx = WXAPI(WX_APPID, WX_APPSECRET)
            r = wx.request_token(ticket)
            logging.debug("request token:%s", r)
            if r.get('errcode'):
                logging.error("request token error:%s %s", 
                              r['errcode'], r['errmsg'])
                return None
     
            access_token = r['component_access_token']
            expires = r['expires_in']
            #提前10分钟过期
            if expires > 20*60:
                expires = expires - 10*60
            logging.debug("request component access token:%s expires:%s", 
                          access_token, r['expires_in'])
            WX.set_componet_access_token(rds, access_token, expires)
            
            component_token = access_token
     
        return component_token

    @staticmethod
    def get_token(rds, wx_appid, refresh_token):
        token = weixin.get_access_token(rds, wx_appid)
        if not token:
            component_token = WXPush.get_component_access_token(rds)
            if not component_token:
                return None

            wx_api = WXAPI(WX_APPID, WX_APPSECRET, component_token)

            r = wx_api.refresh_auth(wx_appid, refresh_token)

            if r.get('errcode'):
                logging.error("refresh auto error:%s %s", 
                              r['errcode'], r['errmsg'])
                return None

            token = r['authorizer_access_token']
            expires = r['expires_in']
            authorizer_refresh_token = r['authorizer_refresh_token']

            #提前10分钟过期
            if expires > 20*60:
                expires = expires - 10*60

            if authorizer_refresh_token != refresh_token:
                logging.error("old refresh token:%s new refresh token:%s", 
                              refresh_token, authorizer_refresh_token)
            else:
                logging.debug("refresh token is unchanged")

            weixin.set_access_token(rds, wx_appid, token, expires)
            
        return token

    @classmethod
    def get_wx_app(cls, appid):
        now = int(time.time())
        app = cls.apps[appid] if cls.apps.has_key(appid) else None
        EXPIRE = 5*60
        if app is None or now - app['timestamp'] > EXPIRE:
            obj = application.get_wx(cls.mysql, appid)
            if not obj:
                return None
            app = {}
            app["appid"] = appid
            app["timestamp"] = now
            app["gh_id"] = obj['gh_id']
            app["wx_appid"] = obj['wx_app_id']
            app["wx_refresh_token"] = obj['refresh_token']
            app["store_id"] = obj['store_id']
            cls.apps[appid] = app
        return app


    @staticmethod
    def send_text(token, openid, text):
        """
        向用户发送文本消息
        """
        wx = WX(token)
        result = wx.send_text_message(openid, text)
        return _check_error(result)

    @staticmethod
    def send_image(token, openid, files):
        """
        发送图片
        """
        wx = WX(token)
        if wx:
            if isinstance(files, str) or isinstance(files, unicode):
                res = requests.get(files)
                content = res.content
            else:
                media = files['media']
                content = media.stream
            filename = random_ascii_string(10) + '.jpg'
            result_1 = wx.add_media('image', [
                ('image', (filename, content, 'image/jpeg'))
            ])
            result_1 = _check_error(result_1)
            media_id = result_1.get('media_id')
            result_2 = wx.send_common_message(openid, msgtype='image', content={
                'media_id': media_id
            })
            return _check_error(result_2)

    @staticmethod
    def send_voice(token, openid, files):
        """
        发送语音
        """
        wx = WX(token)
        if wx:
            if isinstance(files, str) or isinstance(files, unicode):
                res = requests.get(files)
                content = res.content
            else:
                media = files['media']
                content = media.stream
            filename = random_ascii_string(10) + '.amr'
            result_1 = wx.add_media('voice', [
                ('voice', (filename, content, 'audio/amr'))
            ])
            result_1 = _check_error(result_1)
            media_id = result_1.get('media_id')
            result_2 = wx.send_common_message(openid, msgtype='voice', content={
                'media_id': media_id
            })
            return _check_error(result_2)

    @staticmethod
    def send_article(wx_appid, wx_app_secret, token, openid, articles):
        """
        向用户发送文章
        """
        wx = WX(wx_appid, wx_app_secret, token)
        if wx:
            for article in articles:
                if not article.get('title'):
                    article['title'] = ''
                if not article.get('description'):
                    article['description'] = ''
            result = wx.send_common_message(openid, msgtype='news', content={
                'articles': articles
            })
            return _check_error(result)

    @staticmethod
    def send_template(wx_appid, wx_app_secret, token, template_id, openid, title, text):
        """
        向用户发送模板消息
        """
        wx = WX(wx_appid, wx_app_secret, token)
        n = int(time.time())
        arr = time.localtime(n)

        user = wx.get_user_by_openid(openid)
        if not user or user.get('subscribe') == 0:
            return False
        if not template_id:
            return False

        result = wx.send_template_message(openid, {
            'template_id': template_id,
            'data': {
                'first': {
                    'value': title
                },
                'keyword1': {
                    'value': user.get('nickname')
                },
                'keyword2': {
                    'value': time.strftime(u'%Y年%m月%d日 %H:%M'.encode('utf-8'), arr).decode('utf-8')
                },
                'remark': {
                    'value': text
                }
            }
        })
        return _check_error(result)

        
    @classmethod
    def push(cls, appid, appname, openid, content):
        app = WXPush.get_wx_app(appid)
        if app is None:
            logging.warning("can't read wx gh id")
            return False

        token = WXPush.get_token(cls.rds, app['wx_appid'], app['wx_refresh_token'])
        if not token:
            logging.warning("can't get wx token")
            return False

        obj = json.loads(content)
        if obj.has_key("text"):
            alert = obj["text"]
            WXPush.send_text(token, openid, alert)
            return True
        elif obj.has_key("audio"):
            WXPush.send_voice(token, openid, obj['audio']['url'])
            return True
        elif obj.has_key("image"):
            WXPush.send_image(token, openid, obj['image'])
            return True
        else:
            alert = u"你收到了一条消息"
            return False         


if __name__ == "__main__":
    gh_id = ""
    wx_app_id = ''
    wx_secret = ""
    template_id = ''
    openid = ""
    text = "test"
    WXPush.send_text(wx_app_id, wx_secret, openid, text)
