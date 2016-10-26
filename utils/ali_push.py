# -*- coding: utf-8 -*-


import json

from aliyunsdkpush.request.v20150827 import PushRequest
from aliyunsdkcore import client
import time
from datetime import datetime
import xmltodict

from logging import getLogger

LOGGER = getLogger()


class Push(object):
    # 推送目标
    TARGET_DEVICE = 'device'  # 设备
    TARGET_ACCOUNT = 'account'  # 帐号
    TARGET_ALIAS = 'alias'  # 别名
    TARGET_TAG = 'tag'  # 标签
    TARGET_ALL = 'all'  # 全部

    TARGET_VALUE_ALL = 'all'

    # 设备类型
    DEVICE_TYPE_ALL = 3  # 全部设备
    DEVICE_TYPE_IOS = 0  # IOS设备
    DEVICE_TYPE_ANDROID = 1  # Android设备

    # 消息类型
    TYPE_MESSAGE = 0  # 消息
    TYPE_NOTICE = 1  # 通知

    # Android点击通知后打开类型
    ANDROID_OPEN_TYPE_OPEN_APP = 1  # 打开应用
    ANDROID_OPEN_TYPE_OPEN_ACTIVITY = 2  # 打开应用Activity
    ANDROID_OPEN_TYPE_OPEN_URL = 3  # 打开 url

    # APNS环境
    APNS_ENV_DEV = 'DEV'
    APNS_ENV_PRODUCT = 'PRODUCT'

    def __init__(self, access_key_id, access_key_secret, app_key, region_id='cn-hangzhou'):
        # 编码为unicode时签名失败，编码需要转成utf8
        self.access_key_id = access_key_id.encode('utf8') if isinstance(access_key_id, unicode) else access_key_id
        self.access_key_secret = access_key_secret.encode('utf8') if isinstance(access_key_secret,
                                                                                unicode) else access_key_secret
        self.region_id = region_id.encode('utf8') if isinstance(region_id, unicode) else region_id
        self.app_key = int(app_key)

        self.client = client.AcsClient(self.access_key_id, self.access_key_secret, self.region_id)

    def send(self, title, body, target=TARGET_ALL, accounts=None, summary=None, payload=None,
             push_type=TYPE_MESSAGE,
             device_type=DEVICE_TYPE_ALL,
             push_time=None, expire_time=None,
             android_options=None,
             ios_options=None):
        """
        :param title: 标题 Android推送时通知的标题/消息的标题,最长20个字符，中文算1个字符
        :type title: str
        :param body: Android推送时通知的内容/消息的内容；iOS消息内容
        :type body: str
        :param target: 目标
        :type target: str
        :param accounts: 帐号ID的数组(帐号与设备有一次最多100个的限制) 或者 字符串 all
        :type accounts: list, str
        :param summary: iOS通知内容
        :type summary: str
        :param payload: 消息内容
        :type payload: dict
        :param push_type 推送类型
        :type push_type int
        :param device_type: 针对平台 ANDROID或IOS
        :type device_type: int
        :param push_time: 定时发送消息。秒为单位的时间的时间戳,或者datetime 或 %Y-%m-%d %H:%M:%S格式string
        :type push_time: int,datetime,string
        :param expire_time: 定时发送消息。秒为单位的时间的时间戳,或者datetime 或 %Y-%m-%d %H:%M:%S格式string
        :type expire_time: int,datetime,string
        :param android_options: Android平台推送选项
        :type android_options: dict
        :param ios_options: iOS平台推送选项
        :type ios_options: dict
        :return: dict
        """

        request = PushRequest.PushRequest()
        request.set_AppKey(self.app_key)

        request.set_Target(target)

        if target == self.TARGET_ALL:
            request.set_TargetValue(self.TARGET_VALUE_ALL)
        elif target in [self.TARGET_ACCOUNT, self.TARGET_DEVICE, self.TARGET_ALIAS, self.TARGET_TAG]:
            if not accounts:
                return False

            elif isinstance(accounts, list):
                if len(accounts) > 100:
                    return False

                request.set_TargetValue(','.join([str(aid) for aid in accounts]))
            else:
                request.set_TargetValue(accounts)
        else:
            return False

        request.set_Type(push_type)

        request.set_DeviceType(device_type)

        request.set_Title(title)

        request.set_Body(body)
        # iOS通知的内容

        if summary is None:
            if body is not None:
                request.set_Summary(body)
        else:
            request.set_Summary(summary)

        if not ios_options:
            ios_options = {}

        ios_options.setdefault('remind', True)

        # 推送IOS配置
        if ios_options:
            if 'badge' in ios_options:
                request.set_iOSBadge(ios_options['badge'])  # iOS应用图标右上角角标

            if 'music' in ios_options:
                request.set_iOSMusic(ios_options['music'])  # iOS通知声音

            if 'apns_env' in ios_options:  # DEV
                request.set_ApnsEnv(ios_options['apns_env'])  # iOS推送环境

            if 'remind' in ios_options:
                request.set_Remind(ios_options['remind'])  # 当APP不在线时候，是否通过通知提醒

        # 推送android配置
        if android_options:
            if 'music' in android_options:
                request.set_AndroidMusic(android_options['music'])  # iOS通知声音

            if 'open_type' in android_options:
                if android_options['open_type'] == self.ANDROID_OPEN_TYPE_OPEN_URL and 'open_url' in android_options:
                    request.set_AndroidOpenType(self.ANDROID_OPEN_TYPE_OPEN_URL)
                    request.set_AndroidOpenUrl(
                        android_options['open_url'])  # Android收到推送后打开对应的url,仅仅当androidOpenType=3有效
                elif android_options['open_type'] == self.ANDROID_OPEN_TYPE_OPEN_ACTIVITY \
                        and 'activity' in android_options:
                    request.set_AndroidOpenType(self.ANDROID_OPEN_TYPE_OPEN_ACTIVITY)
                    request.set_AndroidActivity(android_options['activity'])
                else:
                    request.set_AndroidOpenType(self.ANDROID_OPEN_TYPE_OPEN_APP)

        # ext parameters
        if payload:
            request.set_iOSExtParameters(json.dumps(payload))
            request.set_AndroidExtParameters(json.dumps(payload))

        if push_time:
            # YYYY-MM-DDThh:mm:ssZ
            request.set_PushTime(self.get_utc_time(push_time))

        if expire_time:
            request.set_StoreOffline(True)  # 离线消息是否保存,若保存, 在推送时候，用户即使不在线，下一次上线则会收到
            request.set_ExpireTime(self.get_utc_time(expire_time))  # 失效时间, 过期时间时长不会超过发送时间加72小时
        else:
            request.set_StoreOffline(False)

        # request.set_BatchNumber("10010")  # 批次编号,用于活动效果统计. 设置成业务可以记录的字符串

        result = self.client.do_action(request)
        if result:
            res = xmltodict.parse(result)
            if res and res.get('PushResponse', {}).get('ResponseId'):
                return True
            else:
                print result
        return False

    @classmethod
    def get_utc_time(cls, order_time):
        if isinstance(order_time, (str, unicode)):
            order_time = datetime.strptime(order_time, '%Y-%m-%d %H:%M:%S')
            timestamp = time.mktime(order_time.timetuple())
        elif isinstance(order_time, int):
            timestamp = order_time
        elif isinstance(order_time, datetime):
            timestamp = time.mktime(order_time.timetuple())
        else:
            timestamp = int(time.time())

        return cls.local2utc(timestamp)

    @staticmethod
    def local2utc(timestamp):
        utc_time = datetime.utcfromtimestamp(timestamp)
        return utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')


if __name__ == '__main__':
    import os

    print Push.get_utc_time(datetime.now())
    print Push.get_utc_time(int(time.time()))
    print Push.get_utc_time('2016-05-20 12:00:00')

    push = Push(os.getenv('ACCESS_KEY_ID'), os.getenv('ACCESS_SECRET'), os.getenv('APP_KEY'))

    # 发送的device id列表, 逗号分隔 比如:  111 或是  111,222
    device_ids = '4b899662464d4e3580d48a56893d146f'

    # 发送的accounts 列表, 逗号分隔 比如:  account1 或是  account1,account2
    # account_ids = ['1']

    print push.send(accounts=device_ids, target=Push.TARGET_DEVICE, title='通知', body='内容',
                    push_type=Push.TYPE_NOTICE)
