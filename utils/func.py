# -*- coding: utf-8 -*-
import re
import string
import urllib
import urlparse
import random
import base64
from itertools import izip, cycle
import time

LETTERS = 0b001
DIGITS = 0b010
PUNCTUATION = 0b100


def valid_email(email):
    email = str(email)
    if len(email) > 7:
        pattern = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        if re.match(pattern, email) is not None:
            return True

    return False


def random_ascii_string(length, mask=None):
    if mask is None:
        mask = LETTERS | DIGITS

    unicode_ascii_characters = ''
    if mask & LETTERS:
        unicode_ascii_characters += string.ascii_letters.decode('ascii')
    if mask & DIGITS:
        unicode_ascii_characters += string.digits.decode('ascii')
    if mask & PUNCTUATION:
        unicode_ascii_characters += string.punctuation.decode('ascii')

    if not unicode_ascii_characters:
        return ''

    rnd = random.SystemRandom()
    return ''.join([rnd.choice(unicode_ascii_characters) for _ in xrange(length)])


def url_query_params(url):
    """
    从特定的url中提取出query string字典
    """
    return dict(urlparse.parse_qsl(urlparse.urlparse(url).query, True))


def url_dequery(url):
    """
    去掉url中query string
    """
    url = urlparse.urlparse(url)
    return urlparse.urlunparse((url.scheme,
                                url.netloc,
                                url.path,
                                url.params,
                                '',
                                url.fragment))


def build_url(base, additional_params=None):
    """
    url中增加query string参数
    """
    url = urlparse.urlparse(base)
    query_params = {}
    query_params.update(urlparse.parse_qsl(url.query, True))
    if additional_params is not None:
        query_params.update(additional_params)
        for k, v in additional_params.iteritems():
            if v is None:
                query_params.pop(k)

    return urlparse.urlunparse((url.scheme,
                                url.netloc,
                                url.path,
                                url.params,
                                urllib.urlencode(query_params),
                                url.fragment))


def xor_crypt_string(data, key, encode=False, decode=False):
    if decode:
        missing_padding = 4 - len(data) % 4
        if missing_padding:
            data += b'=' * missing_padding
        data = base64.decodestring(data)
    xored = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(key)))
    if encode:
        return base64.encodestring(xored).strip().strip('=')
    return xored


COUNTRY_ZONE = ('86',)


def parse_mobile(mobile_str):
    if mobile_str:
        match = re.findall(r'^(\+({0}))?(\d+)$'.format('|'.join(COUNTRY_ZONE)), mobile_str)
        if match:
            zone, mobile = match[0][-2:]
            if '+' in mobile_str and not zone:
                return None
            if not zone:
                zone = '86'
            return valid_mobile(zone, mobile)
    return None


def valid_mobile(mobile_zone, mobile):
    if mobile_zone == '86' and re.match(r'^1\d{10}$', mobile) is not None:
        return mobile_zone, mobile

    return None


def int_to_date(n, pattern='%Y%m%d'):
    return time.strftime(pattern, time.localtime(n))


def date_to_int(s, pattern='%Y-%m-%d'):
    arr = time.strptime(s, pattern)
    return time.mktime(arr)



def is_chars(s):
    return all(c in string.printable for c in s)


def different(list1, list2):
    """
    得到 list2中有,而list1中没有的数据
    :param list1:
    :param list2:
    :return:
    """
    return list(set(list2).difference(set(list1)))


def remove_duplicates(arr):
    data = []
    for v in arr:
        if v not in data:
            data.append(v)
    return data


def filter_dict(d, keys):
    params = {}
    for key in keys:
        params[key] = d.get(key)
    return params


def gen_kv_object(*values):
    class C(object):
        pass

    for key in values:
        setattr(C, key, key)
    C.values = values
    C.length = len(values)
    return C


def pagination(data, offset, limit, total, to_dict=False):
    if to_dict:
        data = [item.to_dict() for item in data]
    return {
        'data': data,
        'pagination': {
            'offset': offset + limit,
            'limit': limit,
            'rows_found': total
        }
    }


def pager_params(offset=0, limit=10):
    offset = int(offset or 0)
    limit = int(limit or 10)
    return offset, limit
