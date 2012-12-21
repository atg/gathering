import sys
import os
import sqlite3
import traceback
import subprocess
import re
import inspect
import json
from pprint import pprint

printExceptions = True
db = None

def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)

def addRowRaw(module, parent, name, original_namespace, kind, defline, docs, linedecl, **others):
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    print '%s, %s  [%s] // %d' % (kind, qualname, defline, len(docs))
    #print docs

    fullsource = others['fullsource'] if 'fullsource' in others else ''
    superclass = others['superclass'] if 'superclass' in others else ''
    
    visibility = others['visibility'] if 'visibility' in others else ''
    canread = others['canread'] if 'canread' in others else ''
    canwrite = others['canwrite'] if 'canwrite' in others else ''
    issingleton = others['issingleton'] if 'issingleton' in others else ''
    
    c = db.cursor()
    c.execute("""INSERT INTO symbols (
        namespace, parents, name, original_namespace,
        type_code, declaration, documentation, sourcedecl,
        fullsource, superclass,
        visibility, canread, canwrite, issingleton) VALUES (
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?, ?)""", (
        module, parent, name, original_namespace,
        kind, defline, removeNonAscii(docs), linedecl,
        fullsource, superclass,
        visibility, canread, canwrite, issingleton))

def splitlinesstrip(s):
    return [line.strip() for line in s.splitlines() if line.strip()]

INPATH = ''

def main(argv):
    if len(argv) != 3:
        print "gath-rb.py <language> <input> <output>"
        return 1
    
    language, inpath, outpath = argv
    if not outpath.endswith('.db'):
        print "output path must end with .db"
        return 1
    
    global INPATH
    INPATH = inpath
    
    try: os.unlink(outpath)
    except: pass
    
    jsonstr = subprocess.check_output(['/usr/bin/env', 'ruby', 'script/gath-rb-ri.rb', inpath]).strip()
    print 'End'
    print jsonstr
    j = json.loads(jsonstr)
    if not j or len(j) < 3:
        return 0
    
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
        visibility TEXT, canread BOOLEAN, canwrite BOOLEAN, issingleton BOOLEAN,
        superclass TEXT,
        
        weighting REAL)""")
    c.execute("CREATE INDEX symbols_index ON symbols (name COLLATE NOCASE)")
    
    print 'Begin'
    
    modules = []
    for record in j:
        if record['type'] == 'namespace':
            modules.append(record['fullname'])
    
    allowedkeys = {'fullsource', 'superclass', 'visibility', 'canread', 'canwrite', 'issingleton'}
    
    with db:
        for record in j:
            #print record['fullname']
            if record['type'] == 'method' or record['type'] == 'property':
                parents, _, name = record['fullname'].rpartition('#')
            else:
                parents, _, name = record['fullname'].rpartition('::')
        
            namespace = ''
            newparents = parents
            for mod in modules:
                if parents.startswith(mod + '::') and len(mod) > len(namespace):
                    namespace = mod
                    newparents = parents[len(mod + '::'):]
            parents = newparents
        
            #print '  ' + str((namespace, parents, name))
            #pprint(record)
        
            if 'fullsignature' in record:
                fullsignature = record['fullsignature']
            elif 'signature' in record:
                fullsignature = record['signature']
            elif 'minisignature' in record:
                fullsignature = record['minisignature']
        
            if 'minisignature' in record:
                signature = record['minisignature']
            elif 'signature' in record:
                signature = record['signature']
            elif 'fullsignature' in record:
                signature = record['fullsignature']
        
            # TODO: CONSTANTS
            # html = 
            recordargs = { k: record[k] for k in record if k in allowedkeys }            
            
            addRowRaw(namespace, parents, name,
                      namespace, record['type'],
                      signature, record['html'], fullsignature,
                      **recordargs)
        
    # print modules
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
