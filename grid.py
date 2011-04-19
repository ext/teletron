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

class Clu:
    access = 0
    alias = ['clu']

    @expose
    def code(self, num, *args):
        """Modify memory on your disc
Usage: CODE <NUMBER> [ARGS..]"""

        try:
            num = int(num)
        except ValueError:
            print >> self, 'INVALID LOCATION'
            return

        # troll kommandon
        if num == 42:
            print >> self, 'GOT ANSWER TO THE ULTIMATE QUESTION OF LIFE, THE UNIVERSE, AND EVERYTHING. QUESTION FORGOTTEN.'
            return

        if num == 1337:
            print >> self, 'ARE YOU A WIZARD?'
            return

        if num > 9000:
            print >> self, "IT'S OVER NINE-THOUSAND!"
            return

        # riktiga
        if num == 6:
            self.code_6(args)

        if num == 872:
            self.code_872(args)

    def code_6(self, args):
        if len(args) != 4:
            print >> self, 'NO LOCATION SPECIFIED'
            return
        
        if args[0].lower() != 'password':
            print >> self, 'MALFORMED COMMAND'
            print 'pwd'
            return

        if args[1].lower() != 'to':
            print >> self, 'MALFORMED COMMAND'
            print 'to'
            return

        if args[2].lower() != 'memory':
            print >> self, 'MALFORMED COMMAND'
            print 'mem'
            return

        try:
            loc = args[3]
            print 'loc', loc
            if loc == '0222':
                tmp = self.disc.access
                self.disc.access = 1
                self.disc.commit(self.conn, self)
                if tmp == 0:
                    print >> self, 'PASSWORD: tonfiskchili19'
                    return
            elif int(loc) % 5 == 0 or int(loc) % 13 == 0 or int(loc) % 42 == 0:
                self.disc.corrupt = 1
                self.disc.commit(self.conn, self)
                return
            else:
                print >> self, 'INVALID LOCATION'
                return
        except:
            traceback.print_exc()
            print >> self, 'MALFORMED COMMAND'

    def code_872(self, args):
        line = ' '.join(args).lower()
        if line != 'override port control':
            print >> self, 'MALFORMED COMMAND'
        if self.disc.attack != 1:
            print >> self, 'NOT IN ATTACK MODE, USE RINZLER TO ENGAGE'
        self.disc.access = 2
        self.disc.commit(self.conn, self)
        print >> self, 'PASSWORD: sottjej17'

class MCP:
    access = 10
    alias = ['master control program', 'master control', 'mcp']

class Rinzler:
    access = 1
    alias = ['rinzler', 'r']

    @expose
    def initiate(self, *args):
        if len(args) < 3 or \
                args[0].lower() != 'attack' or \
                args[1].lower() != 'on':
            raise ValueError

        target = ' '.join(args[2:]).lower()
        program = self.resolve_program(target)
        
        if program is None:
            print >> self, 'UNKNOWN PROGRAM', target
            return

        print >> self, 'INITIATING ATTACK ON', target.upper()
        if target not in MCP.alias:
            print >> self, "IT'S SUPER EFFECTIVE"
            self.blacklist.append(program.alias[0])
        else:
            self.disc.attack = 1
            print >> self, 'RUN CODE 872 TO PROCEED'

class Quorra:
    access = 2
    alias = ['quorra', 'q']

    @expose
    def introduce(self, who):
        who = who.lower()
        if who == 'castor':
            print >> self, 'THIS IS NOT HIS REAL NAME'
            return

        if who == 'zuze':
            print >> self, 'YOU HAVE BEEN INTRODUCED TO ZUZE'
            print >> self, 'YOU CAN FIND ZUZE AT THE END OF LINE BAR'
            print >> self, 'RUN CODE 149 TO PROCEED'
            print >> self, 'FIND DOCUMENTATION AT <insert rajula here>'
            return
        
        print >> self, 'I DO NOT KNOW WHO THAT IS'

class Zuze:
    access = 3
    alias = ['zuze', 'z']

class Client(threading.Thread):
    programs = [Clu, Rinzler, MCP, Quorra]
    files = {
        'GARBAGE': 'troll',
        'nxgame': '''<insert text here>'''
    }

    def __init__(self, sock, addr):
        threading.Thread.__init__(self)
        self.sock = sock
        self.addr = addr
        self.alive = True
        self.buf = ''
        self.disc = None
        self.program = None
        self.blacklist = []
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
            self.sock.send(self.buf + "\r")
            self.buf = ""
            return

    def __iter__(self):
        cmd = [(name,func.__doc__) for name,func in Client.__dict__.items() if getattr(func, '_exposed_', False) and func.__doc__]
        if self.program:
            cmd += [(name,func.__doc__) for name,func in self.program.__dict__.items() if getattr(func, '_exposed_', False) and func.__doc__]
        return cmd.__iter__()

    def __getitem__(self, key):
        src = [Client.__dict__]
        if self.program:
            src.append(self.program.__dict__)

        for x in src:
            func = x.get(key.lower(), None)
            if func is None:
                continue
            if getattr(func, '_exposed_') == None:
                continue
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
        """Identifies yourself"""
        try:
            self.disc = Disc(self.conn, identity)
            print >> self, 'WELCOME', self.disc.username
            if 'god' in self.disc.extra:
                print >> self, 'G-G-G-OD MODE ENABLED'
        except ValueError, e:
            print '[%s] --- %s' % (self.addr, str(e))
            print >> self, 'CORRUPT DISC'

    @expose
    def ls(self):
        for x in Client.files.keys():
            print >> self, x

    @expose
    def cat(self, *args):
        self.show(*args)

    @expose
    def show(self, *args):
        for x in args:
            if x not in Client.files:
                print >> self, 'NO SUCH FILE:', x
                return
            if x == 'GARBAGE' and self.disc.access < 10:
                print >> self, 'ACCESS RESTRICTED:', x
                return
            
            print >> self, Client.files[x]

    @expose
    def logout(self):
        """Logout from the grid"""
        self.stop()

    @expose
    def whoami(self):
        """Show disc information"""
        print >> self, repr(self.disc)

    def resolve_program(self, name):
        for x in Client.programs:
            for y in x.alias:
                if y != name:
                    continue

                if x.alias[0] in self.blacklist:
                    return None

                if x.access > self.disc.access:
                    return False

                return x
    @expose
    def rq(self, *args):
        self.request('access', 'to', *args)

    @expose
    def request(self, *args):
        """INITIATES A REQUEST
ACCESS: REQUESTS ACCESS TO A PROGRAM.
USAGE: REQUEST ACCESS TO <PROGRAM NAME>"""
        if len(args) < 3:
            raise TypeError
        if args[0].lower() != 'access' or args[1].lower() != 'to':
            raise TypeError

        name = ' '.join(args[2:]).lower()
        program = self.resolve_program(name)

        if program is None:
            print >> self, 'UNKNOWN PROGRAM'
        elif program == False:
            print >> self, 'ACCESS DENIED'
        else:
            print >> self, 'ACCESS GRANTED. %s PROGRAM ACTIVATED' % program.alias[0].upper()
            self.program = program

            if self.disc.access == 0:
                print >> self, 'PASSWORD: kycklingcurry'            

    @expose
    def exit(self):
        if self.program:
            self.program = None
        else:
            self.stop()

    @expose
    def whosyourdaddy(self):
        if self.disc.uid > 100:
            self.disc.corrupt = 1
        else:
            self.disc.extra['god'] = 1            
        self.disc.commit(self.conn, self)

    @expose
    def _generate_identity_(self, uid, username):
        try:
            disc = Disc(self.conn, values={'uid': uid, 'u': username})
            row = self.conn.execute('SELECT MAX(instance) FROM disc WHERE user_id=?', (disc.uid,)).fetchone()
            if row[0] is not None:
                disc.instance = row[0]+1
            else:
                disc.instance = 0
            disc.commit(self.conn, self)
        except:
            traceback.print_exc()
            raise

    def run(self):
        sock = self.sock # shortcut
        self.conn = sqlite3.connect('disc.db')

        print >> sys.stderr, '[%s] new client connected' % str(self.addr)
        print >> self, 'WELCOME TO THE NX GRID'
        print >> self, 'INSERT DISC'

        need_prompt = True
        while self.alive:
            try:
                if need_prompt:
                    if self.program:
                        sock.send('%s > ' % self.program.alias[0])
                    else:
                        sock.send('> ')
                    need_prompt = False

                rd, rw, rx = select([sock], [], [sock], 1.0)

                if len(rx) == 1:
                    self.stop()
                    continue

                if len(rd) == 0:
                    continue

                need_prompt = True
                line = sock.recv(4096)
                
                if line in [chr(3), chr(4), chr(255) + chr(244) + chr(255) + chr(253) + chr(6)]:
                    sock.send("\r\n")
                    self.exit()
                    continue

                line = line.strip()
                print '[%s] <<< %s' % (self.addr, line)
                line = line.split(' ')

                cmd = line[0].lower()
                args = line[1:]

                if self.disc == None and cmd not in ['exit', 'login', '_generate_identity_']:
                    print >> self, 'INSERT DISC'
                    continue

                func = self[cmd]
                if func is None:
                    print >> self, 'UNKNOWN COMMAND'
                    continue

                try:
                    func(self, *args)
                except TypeError:
                    print >> self, 'MALFORMED COMMAND'
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
