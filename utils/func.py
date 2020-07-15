# -*- coding: utf-8 -*-
import re
import string
import random
import base64
import time

LETTERS = 0b001
DIGITS = 0b010
PUNCTUATION = 0b100



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

