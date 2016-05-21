# -*- coding: utf-8 -*-
import time
import requests
from utils.func import random_ascii_string
from utils.wx import WX
import pickle
import json
import application


class WXUser(object):
    @classmethod
    def set_seller_id(cls, rds, gh_id, openid, seller_id):
        key = "wx_users_%s_%s"%(gh_id, openid)
        rds.hset(key, "seller_id", seller_id)


def _check_error(result):
    if result and result.get('errcode') > 0:
        logging.error("errmsg:%s", result.get('errmsg') or '公众号发送消息未知异常')
    return result



class WXToken(object):
    @staticmethod
    def get_token(rds, wx_appid):
        """
        获取token
        :param force:  不使用缓存token，直接请求新token
        """

        token = rds.get('wx_token_' + wx_appid)
        if token:
            token = pickle.loads(token)
            access_token = token.get('access_token')
            expire = token.get('expire')
            if expire > int(time.time()):
                return access_token

        return None

    @staticmethod
    def set_token(rds, wx_appid, access_token, expire):
        value = pickle.dumps({'access_token': access_token,'expire': expire})
        rds.set('wx_token_' + wx_appid, value)

    @staticmethod
    def clean_token(rds, wx_appid):
        rds.delete('wx_token_' + wx_appid)

    
class WXPush(object):
    mysql = None
    rds = None
    apps = {}

    @staticmethod
    def get_token(rds, wx_appid, wx_app_secret):
        token = WXToken.get_token(rds, wx_appid)
        if not token:
            wx = WX(wx_appid, wx_app_secret)
            result = wx.request_token()
            if not result:
                return None
            access_token = result.get('access_token')
            exipres_in = result.get('expires_in')
            expire = int(time.time()) + exipres_in - 100
            WXToken.set_token(rds, wx_appid, access_token, expire)
            token = access_token

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
            app["wx_app_secret"] = obj['wx_app_secret']
            app["template_id"] = obj['template_id']
            cls.apps[appid] = app
        return app


    @staticmethod
    def send_text(wx_appid, wx_app_secret, token, openid, text):
        """
        向用户发送文本消息
        """
        wx = WX(wx_appid, wx_app_secret, token)
        result = wx.send_text_message(openid, text)
        return _check_error(result)

    @staticmethod
    def send_image(wx_appid, wx_app_secret, token, openid, files):
        """
        发送图片
        """
        wx = WX(wx_appid, wx_app_secret, token)
        if wx:
            if isinstance(files, str):
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
    def send_voice(wx_appid, wx_app_secret, token, openid, files):
        """
        发送语音
        """
        wx = WX(wx_appid, wx_app_secret, token)
        if wx:
            if isinstance(files, str):
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

        token = WXPush.get_token(cls.rds, app['wx_appid'], app['wx_app_secret'])
        if not token:
            logging.warning("can't get wx token")
            return False

        obj = json.loads(content)
        if obj.has_key("text"):
            alert = obj["text"]
            WXPush.send_text(app['wx_appid'], app['wx_app_secret'], token, openid, alert)
            return True
        elif obj.has_key("audio"):
            alert = u"你收到了一条消息"
            return False
        elif obj.has_key("image"):
            alert = u"你收到了一张图片"
            return False
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
