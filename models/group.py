# -*- coding: utf-8 -*-


def get_group_name(db, group_id):
    sql = "SELECT name FROM `group` WHERE id=%s"
    cursor = db.execute(sql, group_id)
    r = cursor.fetchone()
    if r:
        return r["name"]
    else:
        return None
