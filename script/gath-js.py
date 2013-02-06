#!/usr/bin/env python
# JS library gatherer
# python thegatherer.py py libs/Django-1.4.2/django testdjango.db

'''
    symbols
        namespace parents name kind declaration documentation

'''

import sys
import os
import sqlite3
import traceback
import subprocess
import re
import inspect
import json
from pprint import pprint
from createdb import *

printExceptions = True

db = None

def fauxDefinition(name, fobj):
    hasextras = bool(inspect.getargspec(fobj)[1]) or bool(inspect.getargspec(fobj)[2])
    
    args = inspect.getargspec(fobj)[0]
    defaults = inspect.getargspec(fobj)[3]
    
    if not defaults:
        defaults = []
    for i, x in enumerate(defaults):
        dx = repr(x)
        if ' ' in dx or '\t' in dx or ',' in dx:
            dx = '...'
        args[len(args) - i - 1] = '%s=%s' % (args[len(args) - i - 1], dx)
    
    return '%s(%s)' % (name, '...' if (hasextras and len(args) == 0) else ', '.join(args))

def filename2namespace(f):
    if os.path.basename(f) == '__init__.py':
        return filename2namespace(os.path.dirname(f))
    else:
        return os.path.splitext(f.replace('/', '::'))[0]

def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)



def splitlinesstrip(s):
    return [line.strip() for line in s.splitlines() if line.strip()]

INPATH = ''

def parseJS(filepaths, inpath, outpath):
    for filepath in filepaths:
        jp = 'XXJSONXX'
        print ['/usr/local/bin/node', 'dep/doctorjs/bin/jsctags.js', '-j', jp, '-f', '-', filepath]
        output = subprocess.check_output(['/usr/local/bin/node', 'dep/doctorjs/bin/jsctags.js', '-j', jp, '-f', '-', filepath])
        output = output[len(jp) + 1 : -2]
        j = json.loads(output)
        for symbol in j:
            name = str(symbol['name'])
            if name == '%anonymous_function' or name == '$':
                continue
            
            #pprint(symbol)
            if symbol['kind'] == 'f':
                kind = 'function'
            elif symbol['kind'] == 'v':
                kind = 'variable'
            else:
                continue
            
            defline = str(symbol['addr'])
            if defline:
                defline = defline[2:-2]
            if not defline:
                defline = ''
            #print defline
            addRowRaw(db, '', '', name, '', kind, defline, '', '')
        
        #print output
    
def main(argv):
    if len(argv) != 3:
        print "thegatherer.py <language> <input> <output>"
        return 1
    
    language, inpath, outpath = argv
    if not outpath.endswith('.db'):
        print "output path must end with .db"
        return 1
    
    global INPATH
    INPATH = inpath
    
    try: os.unlink(outpath)
    except: pass
    
    global db
    db = sqlite3.connect(outpath)
    
    c = db.cursor()
    c.execute("""CREATE TABLE symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        namespace TEXT, parents TEXT, name TEXT,
        original_namespace TEXT,
        type_code TEXT,
        declaration TEXT, sourcedecl TEXT, documentation TEXT,
        
        fullsource TEXT,
        visibility TEXT, canread BOOLEAN DEFAULT 1, canwrite BOOLEAN DEFAULT 1, issingleton BOOLEAN DEFAULT 0,
        superclass TEXT,
        isDocumented BOOLEAN DEFAULT 0,
        
        weighting REAL)""")
    c.execute("CREATE INDEX symbols_index ON symbols (name COLLATE NOCASE)")
    
    # Find all relevant files
    filepaths = []
    if os.path.isdir(inpath):
        for root, dirs, files in os.walk(inpath):
            for fp in files:
                ext = os.path.splitext(fp)[1].lower()
                fullpath = os.path.join(root, fp)
                if ext == '.js':
                    filepaths.append(fullpath)
    else:
        filepaths = [inpath]
    
    parseJS(filepaths, inpath, outpath)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
