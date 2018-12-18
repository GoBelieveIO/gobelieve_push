# -*- coding: utf-8 -*-
"""
"""
import logging
import pymysql

LOGGER = logging.getLogger('')


class Cursor(object):
    def __init__(self, c, affected_rows):
        self.c = c
        self.rowcount = affected_rows

    @property
    def lastrowid(self):
        return self.c.lastrowid

    def fetchone(self):
        r = self.c.fetchone()
        return r

    def fetchall(self):
        r = self.c.fetchall()
        return r


class Mysql(object):
    def __init__(self, host, user, password, database, port, charset, autocommit):
        """
        :param host
        :param port
        :param user
        :param password
        :param db
        :param auto_commit
        :param charset
        """
        self._conn = None

        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.charset = charset
        self.autocommit = autocommit

    @property
    def conn(self):
        if not self._conn:
            self._conn = pymysql.connections.Connection(host=self.host, user=self.user,
                                                        password=self.password,
                                                        database=self.database, port=self.port,
                                                        charset=self.charset, autocommit=self.autocommit,
                                                        cursorclass=pymysql.cursors.DictCursor)
        return self._conn

    def execute(self, sql, args=[]):
        evt = {
            'sql': sql,
            'args': args
        }
        LOGGER.debug("sql_execute:{}".format(evt))
        if not isinstance(args, (tuple, list, set)):
            args = (args,)
        with self.conn.cursor() as cursor:
            r = cursor.execute(sql, args)
            return Cursor(cursor, r)

    def begin(self):
        self.conn.begin()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self._conn:        
            self._conn.close()

