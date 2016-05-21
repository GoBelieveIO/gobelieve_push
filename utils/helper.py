# -*- coding: utf-8 -*-
import requests
import urllib

def request_api(url='', method='get', params=None, data=None, files=None, baseurl=''):
    """
    请求API接口
    """
    headers = {}
    if not files:
        headers['content-type'] = 'application/json; charset=utf-8'
    r = getattr(requests, method)(baseurl + url, headers=headers, params=params, data=data, files=files)
    result = r.json()
    return result


def get_redirect_url(app_id, url):
    """
    利用oauth跳转，以便于菜单设置url后得到code从而进一步得到用户的openid
    """
    url = urllib.quote(url)
    redirect_url = 'https://open.weixin.qq.com' \
                   '/connect/oauth2/authorize' \
                   '?appid={appid}' \
                   '&redirect_uri={url}' \
                   '&response_type=code' \
                   '&scope=snsapi_base' \
                   '&state=1' \
                   '#wechat_redirect' \
        .format(appid=app_id, url=url)
    return redirect_url
