# -*- coding: utf-8 -*-
import requests
import time
import json
import socket
try:
    import socks
except Exception:
    pass

APIROOT = 'https://api.weixin.qq.com'
URL = APIROOT + '/cgi-bin/component'

#接口文档
#https://open.weixin.qq.com/cgi-bin/showdocument?action=dir_list&t=resource/res_list&verify=1&id=open1453779503&token=&lang=zh_CN

#公众号第三方平台
class WXAPI(object):
    def __init__(self, app_id='', secret='', token=''):
        """
        连接微信，获取token
        """
        self.app_id = app_id
        self.secret = secret
        self.token = token

    #获取第三方平台component_access_token
    def request_token(self, ticket):
        try:
            url = URL + "/api_component_token"
            obj = {
                "component_appid":self.app_id,
                "component_appsecret":self.secret,
                "component_verify_ticket":ticket
            }
            
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            r = requests.post(url, headers=headers, data=json.dumps(obj))
            result = r.json()
            return result
        except Exception as e:
            return None

    #获取预授权码pre_auth_code
    def request_pre_auth_code(self):
        try:
            url = URL + "/api_create_preauthcode"
            obj = {
                "component_appid":self.app_id,
            }

            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            params = {"component_access_token":self.token}
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            result = r.json()
            return result
        except Exception as e:
            return None

    #使用授权码换取公众号的接口调用凭据和授权信息
    def request_auth(self, authorization_code):
        try:
            url = URL + "/api_query_auth"
            obj = {
                "component_appid":self.app_id,
                "authorization_code":authorization_code
            }

            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            params = {"component_access_token":self.token}
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            
            result = r.json()
            return result
        except Exception as e:
            return None

    #获取（刷新）授权公众号的接口调用凭据（令牌）
    def refresh_auth(self, auth_appid, refresh_token):
        try:
            url = URL + "/api_authorizer_token"
            obj = {
                "component_appid":self.app_id,
                "authorizer_appid":auth_appid,
                "authorizer_refresh_token":refresh_token
            }

            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

            params = {"component_access_token":self.token}
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            
            result = r.json()
            return result
        except Exception as e:
            return None

    #获取授权方的公众号帐号基本信息
    #appid 公众号appid
    def request_info(self, appid):
        try:
            url = URL + "/api_get_authorizer_info"
            obj = {
                "component_appid":self.app_id,
                "authorizer_appid":appid
            }
            params = {"component_access_token":self.token}
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'
            
            r = requests.post(url, params=params, 
                              headers=headers, data=json.dumps(obj))
            result = r.json()
            return result
        except Exception as e:
            return None


class WXAPI2(WXAPI):
    #获取第三方平台component_access_token
    def request_token(self, ticket):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        r = super(WXAPI2, self).request_token(ticket)
        socket.socket = default_socket
        return r

    #获取预授权码pre_auth_code
    def request_pre_auth_code(self):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        r = super(WXAPI2, self).request_pre_auth_code()
        socket.socket = default_socket
        return r
        
    #使用授权码换取公众号的接口调用凭据和授权信息
    def request_auth(self, authorization_code):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        r = super(WXAPI2, self).request_auth(authorization_code)
        socket.socket = default_socket
        return r

    #获取（刷新）授权公众号的接口调用凭据（令牌）
    def refresh_auth(self, auth_appid, refresh_token):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        r = super(WXAPI2, self).refresh_auth(auth_appid, refresh_token)
        socket.socket = default_socket
        return r

    #获取授权方的公众号帐号基本信息
    #appid 公众号appid
    def request_info(self, appid):
        default_socket = socket.socket
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        r = super(WXAPI2, self).request_info(appid)
        socket.socket = default_socket
        return r


    
