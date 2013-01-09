#!/usr/bin/env python
# python thegatherer.py py libs/Django-1.4.2/django testdjango.db

import sys
import os
import sqlite3
import traceback
import subprocess
import re
import inspect
import contextlib

def noexcept():

def extensionsForLanguage(lang):
    if lang == 'py':
        return set(['.py'])
    if lang == 'rb':
        return set(['.rb'])

printExceptions = True

db = None

def fauxDefinition(name, fobj):
    try:
        argspec = inspect.getargspec(fobj)
    except TypeError as e:
        return ''
    
    hasextras = bool(argspec[1]) or bool(argspec[2])
    
    args = argspec[0]
    defaults = argspec[3]
    
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

def processsourcelines(obj):
    fullsource = ''
    linedecl = inspect.getsourcelines(obj)
    if not linedecl:
        return ("", fullsource)
                 
    linedecl = linedecl[0]
    if not linedecl:
        return ("", fullsource)
    
    # Ignore decorators
    while linedecl and linedecl[0].startswith('@'):
        linedecl.pop(0)
    
    if not linedecl:
        return ("", fullsource)
    
    if len(linedecl) < 30:
        fullsource = '\n'.join(linedecl)
    
    linedecl = linedecl[0]
    return (linedecl, fullsource)


def addRow(kind, module, parent, name, fobj, obj, isDocumented):
    if module.endswith('.'):
        module = module[:-1]
    
    defline = ''
    docs = ''
    linedecl = ''
    original_namespace = ''
    superclass = ''
    fullsource = ''
    
    if fobj:
        defline = fauxDefinition(name, fobj)
        if kind == 'class_method' and ('(self, ' in defline or '(self)' in defline):
            kind = 'method'
    if obj:
        try:
            if hasattr(obj, '__module__') and obj.__module__:
                original_namespace = obj.__module__.strip('_')
            else:            
                original_namespace = inspect.getsourcefile(obj)
                if not original_namespace:
                    original_namespace = ''
                else:
                    original_namespace = os.path.relpath(original_namespace, os.path.dirname(INPATH))
                    if original_namespace.startswith('..'):
                        original_namespace = ''
                original_namespace = filename2namespace(original_namespace)
                if original_namespace == 'python2':
                    original_namespace = ''
            print original_namespace
        except TypeError as e:
            pass
        except IOError as e:
            pass
        
        try:
            docs = inspect.getdoc(obj)
            if not docs:
                docs = inspect.getcomments(obj)
                if not docs:
                    docs = ''
            if docs:
                isDocumented = True
        except TypeError as e:
            pass
        except IOError as e:
            pass
        
        try:
            if hasattr(obj, '__bases__'):
                if len(obj.__bases__) == 1:
                    superclass = obj.__bases__[0].__name__
                    if not superclass:
                        superclass = ''
        except TypeError as e:
            pass
        except IOError as e:
            pass

        try:
            linedecl, fullsource = processsourcelines(obj)
        except TypeError as e:
            pass
        except IOError as e:
            pass
    
    module = module.replace('.', '::')
    parent = parent.replace('.', '::')
    
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    addRowRaw(module, parent, name, original_namespace, kind, defline, docs, linedecl, superclass=superclass, fullsource=fullsource, isDocumented=isDocumented)

def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)

def addRowRaw(module, parent, name, original_namespace, kind, defline, docs, linedecl, **others):
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    print '%s, %s  [%s] // %d' % (kind, qualname, defline, len(docs))
    #print docs

    fullsource = others['fullsource'] if 'fullsource' in others else ''
    superclass = others['superclass'] if 'superclass' in others else ''
    isDocumented = others['isDocumented'] if 'isDocumented' in others else False
    
    c = db.cursor()
    c.execute("INSERT INTO symbols (namespace, parents, name, original_namespace, type_code, declaration, documentation, sourcedecl, fullsource, superclass, isDocumented) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (module, parent, name, original_namespace, kind, defline, removeNonAscii(docs), linedecl, removeNonAscii(fullsource), superclass, isDocumented))


modules = set([])

def parsePythonModule(mm, prefix):
    try:        
        mm_all = None
        if hasattr(mm, '__all__'):
            mm_all = mm.__all__
        hasall = bool(mm_all)
        
        for v in dir(mm):
            if v.startswith("_"):
                continue
            
            if mm_all != None:
                if v not in mm_all:
                    continue 
            
            # Does this have documentation? If it doesn't, ignore it
            o = getattr(mm, v)
            d = inspect.getdoc(o)
            isDocumented = True
            if not d:
                d = ''
                
                # Allow undocumented stuff
                if not hasattr(o, 'description') and not hasall:
                    isDocumented = False
                    # continue
                    
                
                # Don't uncomment this, it's for unignoring compiled functions
                #if not (inspect.isroutine(o) and (not inspect.isfunction(o))):
        
            mp = prefix + '.'
            ismatchable = True
            
            #print("%s -- %o %o %o %o" % (mp+v, inspect.ismethod(o), inspect.isfunction(o), inspect.isroutine(o), inspect.isbuiltin(o) ))
            if ismatchable and (inspect.isfunction(o) or inspect.isroutine(o)):
                addRow('function', mp, '', v, o, o, isDocumented)
            elif ismatchable and inspect.ismethod(o):
                addRow('function', mp, '', v, o, o, isDocumented)
            elif inspect.isclass(o):
                addRow('class', mp, '', v, '', o, isDocumented)
                print mp+v
                #if ismatchable: classes.append(mp+v)
                for vv in dir(o):
                    if vv.startswith("_"):
                        continue
                    currentObject = getattr(o, vv)
                    if inspect.isfunction(currentObject) or inspect.isroutine(currentObject):
                        addRow('class_method', mp, v, vv, currentObject, currentObject, isDocumented)
                    elif inspect.ismethod(currentObject):
                        addRow('class_method', mp, v, vv, currentObject, currentObject, isDocumented)
            #elif inspect.ismodule(o):
                #modules.append(v)
            
            modules.add(prefix)
            
    except Exception as e:
        if printExceptions:
            print 'EXCEPTION: ' + str(e)
            print traceback.format_exc() 

import pkgutil

def recParseModule(path, prefix=''):
    try:
        for importer, modname, ispkg in pkgutil.iter_modules([path], ''):
            if modname.startswith('_'):
                continue
            elif modname == 'lib2to3':
                continue
            
            try:
                newPrefix = prefix
                if newPrefix:
                    newPrefix += '.'
                newPrefix += modname
                recParseModule(path + '/' + modname, newPrefix)
                
                mm = __import__(newPrefix, fromlist='blah')
                parsePythonModule(mm, newPrefix)
            except Exception as e:
                if printExceptions:
                    print 'EXCEPTION: ' + str(e)
                    print traceback.format_exc() 
    except Exception as e:
        if printExceptions:
            print 'EXCEPTION: ' + str(e)
            print traceback.format_exc()

def parsePython(filepaths, inpath, outpath):
    lastcomp = os.path.dirname(inpath)
    basecomp = os.path.basename(inpath)
    
    sys.path.insert(0, lastcomp)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'placeholdersettings'
    
    if basecomp in ['python2.7', 'python3.3', 'python3.4', 'python3.5', 'python3.6', 'python3.7', 'python3.8', 'python3.9']:
        basecomp = ''
    
    recParseModule(inpath, basecomp)
    
    for prefix in modules:
        print 'NAMESPACE: ' + prefix
        addRow('namespace', '', '', prefix.replace('.', '::'), '', None, True)

def splitlinesstrip(s):
    return [line.strip() for line in s.splitlines() if line.strip()]

INPATH = ''

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
        visibility TEXT, canread BOOLEAN, canwrite BOOLEAN, issingleton BOOLEAN,
        superclass TEXT,
        
        isDocumented BOOLEAN DEFAULT 0,
                
        weighting REAL)""")
    c.execute("CREATE INDEX symbols_index ON symbols (name COLLATE NOCASE)")
    
    # Find all relevant files
    fileexts = extensionsForLanguage(language)
    filepaths = []
    
    if language == 'py':
        # Do everything in a transaction
        with db:
            parsePython(filepaths, inpath, outpath)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
