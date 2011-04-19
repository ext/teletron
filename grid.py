#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import socket
import traceback
import time
import threading
import sys
import sqlite3
from select import select
from disc import Disc

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
        try:
            self.disc = Disc(self.conn, identity)
            print >> self, 'WELCOME', self.disc.username
        except ValueError, e:
            print '[%s] --- %s' % (self.addr, str(e))
            print >> self, 'CORRUPT DISC'

    @expose
    def whoami(self):
        """Show disc information"""
        print >> self, repr(self.disc)

    @expose
    def _generate_identity_(self, uid, username):
        disc = Disc(self.conn, values={'uid': uid, 'u': username})
        row = self.conn.execute('SELECT MAX(instance) FROM disc WHERE user_id=?', (disc.uid,)).fetchone()
        if row[0] is not None:
            disc.instance = row[0]+1
        else:
            disc.instance = 0
        disc.commit(self.conn)
        print >> self, str(disc)

    def run(self):
        sock = self.sock # shortcut
        self.conn = sqlite3.connect('disc.db')

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

conn = sqlite3.connect('disc.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS
       disc (
       	    id int primary key,	
	    user_id int,
	    instance int,
	    corrupt int,
	    checksum text,
	    UNIQUE(user_id, instance))
''')

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
