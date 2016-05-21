# -*- coding: utf-8 -*-
import time
import logging
import sys
import redis
import json
import uuid
import subprocess
from OpenSSL import crypto
import os
import traceback
import threading
import socket
import binascii
import application
import config
import npush

sandbox = config.SANDBOX

class APNSConnectionManager:
    def __init__(self):
        self.apns_connections = {}
        self.lock = threading.Lock()

    def get_apns_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.apns_connections
            apns = connections[appid] if connections.has_key(appid) else None
        finally:
            self.lock.release()
        return apns

    def remove_apns_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.apns_connections
            if connections.has_key(appid):
                logging.debug("pop client:%s", appid)
                connections.pop(appid)
        finally:
            self.lock.release()

    def set_apns_connection(self, appid, connection):
        self.lock.acquire()
        try:
            self.apns_connections[appid] = connection
        finally:
            self.lock.release()


class SmartPush(object):
    mysql = None
    apns_manager = APNSConnectionManager()
    app_names = {}

        
    @classmethod
    def connect(cls, appid):
        cer, pkey = application.get_certificate(cls.mysql, appid)
        if cer is None or pkey is None:
            return None

        cer_file = "/tmp/android_app_%s.cer" % (appid)
        key_file = "/tmp/android_app_%s.key" % (appid)
        f = open(cer_file, "wb")
        f.write(cer)
        f.close()

        f = open(key_file, "wb")
        f.write(pkey)
        f.close()

        npush_conn = npush.Connection(cer_file, key_file, sandbox=sandbox)
        return npush_conn

    @classmethod
    def get_connection(cls, appid):
        apns = cls.apns_manager.get_apns_connection(appid)
        if not apns:
            apns = cls.connect(appid)
            if not apns:
                logging.warn("get p12 fail client id:%s", client_id)
                return None
            cls.apns_manager.set_apns_connection(appid, apns)
        return apns


    @classmethod
    def push(cls, appid, appname, token, content, extra):
        obj = {}
        obj["title"] = appname
        obj["push_type"] = 1
        obj["is_ring"] = True
        obj["is_vibrate"] = True
        obj["content"] = content
        if extra:
            obj["app_params"] = extra
         
        for i in range(2):
            if i == 1:
                logging.warn("resend notification")
            try:
                npush_conn = cls.get_connection(appid)
                if npush_conn is None:
                    continue

                notification = npush.EnhancedNotification()
                notification.token = token
                notification.identifier = 1
                notification.expiry = int(time.time()+3600)
                notification.payload = json.dumps(obj)
                logging.debug("ng notification:%s", notification.payload)
                npush_conn.reset()
                npush_conn.write_notification(notification)
                break
            except Exception, e:
                print_exception_traceback()
                cls.apns_manager.remove_apns_connection(appid)
                continue

def print_exception_traceback():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logging.warn("exception traceback:%s", traceback.format_exc())
