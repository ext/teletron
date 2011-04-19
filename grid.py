#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import socket
import traceback
import time
import threading
import sys
import csv
import binascii
from select import select
from StringIO import StringIO
from itertools import cycle, islice
def srepeat(string, n):
    return ''.join(islice(cycle(string), n))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 1337))
s.listen(1)

def expose(func):
    func._exposed_ = True
    return func

def access(func, level):
    func._access_ = level
    return func

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

#d = Disc('07120f0702001e455043081515025a1b4e1600154e1717524e5c505a1f1c085c51115f52594f:3340936416')
#print d.uid, d.username


#d = Disc('07120f0702001e455043190213410f1649474f1d4e07060e020f175c48454e5a0649095c4f55571243:2032201623')
#d = Disc('1b5c48454e5a121d4f514f56141d43064f17151a441d50541905165c484d5a5351:2156950058')
#d = Disc('1b5c48454e5a121d4f514f56141d43064f17151a441d50541905165c484d5a53511a5d515a0b52105240425d')
#print d.uid, d.username

#print d

class Client(threading.Thread):
    def __init__(self, sock, addr):
        threading.Thread.__init__(self)
        self.sock = sock
        self.addr = addr
        self.alive = True
        self.buf = ''
        self.disc = None
        print >> sys.stderr, 'New client connected'

    def kill(self):
        self.alive = False
        print >> self, 'NXGAME: server is going down for reboot, come back later. (This is NOT ingame!)'

    def stop(self):
        self.alive = False

    def write(self, data):
        self.buf += data
        if data == "\n":
            print '[%s] >>> %s' % (self.addr, self.buf),
            self.sock.send(self.buf)
            self.buf = ""
            return

    def __iter__(self):
        return [(name,func.__doc__) for name,func in Client.__dict__.items() if getattr(func, '_exposed_', False) and func.__doc__].__iter__()

    def __getitem__(self, key):
        func = Client.__dict__.get(key, None)
        if func is None or getattr(func, '_exposed_') == None:
            return None
        return func

    @expose
    def help(self, command=None):
        if command:
            command = self[command]
            if not command:
                print >> self, 'UNKNOWN COMMAND'
                return
            if command.__doc__ is None:
                print >> self, 'DOCUMENTATION MISSING'
                return
            print >> self, command.__doc__
        else:
            print >> self, 'AVAILABLE COMMANDS:'
            for name,doc in self:
                print >> self, name.upper()

    @expose
    def login(self, identity):
        self.disc = Disc(identity)
        print >> self, 'WELCOME', self.disc.username

    @expose
    def whoami(self):
        """asdf"""
        print >> self, repr(self.disc)

    @expose
    def _generate_identity_(self, uid, username):
        id = Disc(data={'uid': uid, 'u': username})
        print >> self, str(id)

    def run(self):
        sock = self.sock # shortcut

        print >> sys.stderr, '[%s] new client connected' % str(self.addr)
        print >> self, 'WELCOME TO THE NX GRID'
        print >> self, 'INSERT DISC'

        while self.alive:
            try:
                rd, rw, rx = select([sock], [], [], 1.0)
                if len(rd) == 0:
                    continue

                line = sock.recv(4096).strip()
                print '[%s] <<< %s' % (self.addr, line)
                line = line.split(' ')

                cmd = line[0].lower()
                args = line[1:]

                func = Client.__dict__.get(cmd, None)
                if func is None or getattr(func, '_exposed_') == None:
                    print >> self, 'UNKNOWN COMMAND'
                    continue

                try:
                    func(self, *args)
                except TypeError:
                    print >> self, 'MALFORMED COMMAND'
                    traceback.print_exc()
                    continue
            except socket.error:
                raise
            except:
                traceback.print_exc()
        
        try:
            sock.close()
        except:
            traceback.print_exc()

run = True
while run:
    try:
        client = Client(*s.accept())
        client.start()
    except KeyboardInterrupt:
        run = False
    except:
        traceback.print_exc()

for x in threading.enumerate():
    if x == threading.current_thread():
        continue
    x.kill()
