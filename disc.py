#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import csv
import binascii
from StringIO import StringIO
from itertools import cycle, islice
def srepeat(string, n):
    return ''.join(islice(cycle(string), n))

class Disc:
    secret = 'rajulas mamma ar ett troll'

    def __init__(self, identity=None, data=None):
        if identity:
            txt = identity
            n = []
            while len(txt) > 0:
                n.append(int(txt[0:2],16))
                txt = txt[2:]
            
            key = srepeat(Disc.secret, len(n))
            line = ''.join([chr(ord(y) ^ x) for x,y in zip(n, key)])
            [identity, chksum] = line.split(':', 1)
            tmp = binascii.crc32(identity) & 0xffffffff
            if int(chksum,16) != tmp:
                raise ValueError, 'checksum does not match'

            parts = csv.reader(StringIO(identity), delimiter=';', quotechar='"').next()
            data = {}
            for x in parts:
                [key, value] = x.split('=', 1)
                data[key] = value[1:-1]
        
        self.uid = int(data.pop('uid'))
        self.username = data.pop('u')
        self.instance = int(data.pop('i', 0))
        self.access = int(data.pop('a', 0))
        self.extra = data

    def __str__(self):
        d = {
            'uid': self.uid,
            'u': self.username,
            'i': self.instance,
            'a': self.access
        }
        d.update(self.extra)
        l = ['%s="%s"' % x for x in d.items()]

        txt = ';'.join(l)
        chksum = binascii.crc32(txt) & 0xffffffff
        txt = '%s:%010x' % (txt, chksum)
        print txt
        key = srepeat(Disc.secret, len(txt))
        return ''.join(['%02x' % (ord(x) ^ ord(y)) for x,y in zip(txt, key)])

    def __repr__(self):
        return 'uid=%d, username=%s, access=%d, instance=%d' \
            % (self.uid, self.username, self.access, self.instance)
