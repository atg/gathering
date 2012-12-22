#!/usr/bin/env python
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

def extensionsForLanguage(lang):
    if lang == 'py':
        return set(['.py'])
    if lang == 'rb':
        return set(['.rb'])

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

def addRow(kind, module, parent, name, fobj, obj):
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
        original_namespace = inspect.getsourcefile(obj)
        if not original_namespace:
            original_namespace = ''
        else:
            original_namespace = os.path.relpath(original_namespace, os.path.dirname(INPATH))
            if original_namespace.startswith('..'):
                original_namespace = ''
        original_namespace = filename2namespace(original_namespace)
        print original_namespace
        
        docs = inspect.getdoc(obj)
        if not docs:
            docs = inspect.getcomments(obj)
            if not docs:
                docs = ''
        
        if hasattr(obj, '__bases__'):
            if len(obj.__bases__) == 1:
                superclass = obj.__bases__[0].__name__
                if not superclass:
                    superclass = ''
        
        linedecl = inspect.getsourcelines(obj)
        if not linedecl:
            linedecl = ""
        else:
            linedecl = linedecl[0]
            if not linedecl:
                linedecl = ""
            else:
                if len(linedecl) < 30:
                    fullsource = '\n'.join(linedecl)
                
                linedecl = linedecl[0]
    
    module = module.replace('.', '::')
    parent = parent.replace('.', '::')
    
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    addRowRaw(module, parent, name, original_namespace, kind, defline, docs, linedecl, superclass=superclass, fullsource=fullsource)

def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)

def addRowRaw(module, parent, name, original_namespace, kind, defline, docs, linedecl, **others):
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    print '%s, %s  [%s] // %d' % (kind, qualname, defline, len(docs))
    #print docs

    fullsource = others['fullsource'] if 'fullsource' in others else ''
    superclass = others['superclass'] if 'superclass' in others else ''
    c = db.cursor()
    c.execute("INSERT INTO symbols (namespace, parents, name, original_namespace, type_code, declaration, documentation, sourcedecl, fullsource, superclass) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (module, parent, name, original_namespace, kind, defline, removeNonAscii(docs), linedecl, removeNonAscii(fullsource), superclass))


modules = set([])

def parsePythonModule(mm, prefix):
    try:
        for v in dir(mm):
            if v.startswith("_"):
                continue
        
            # Does this have documentation? If it doesn't, ignore it
            o = getattr(mm, v)
            d = inspect.getdoc(o)
            if not d:
                d = ''
                if not hasattr(o, 'description'):
                    continue
        
            mp = prefix + '.'
            ismatchable = True
            
            #print("%s -- %o %o %o %o" % (mp+v, inspect.ismethod(o), inspect.isfunction(o), inspect.isroutine(o), inspect.isbuiltin(o) ))
            if ismatchable and (inspect.isfunction(o) or inspect.isroutine(o)):
                addRow('function', mp, '', v, o, o)
            elif ismatchable and inspect.ismethod(o):
                addRow('function', mp, '', v, o, o)
            elif inspect.isclass(o):
                addRow('class', mp, '', v, '', o)
                print mp+v
                #if ismatchable: classes.append(mp+v)
                for vv in dir(o):
                    if vv.startswith("_"):
                        continue
                    currentObject = getattr(o, vv)
                    if inspect.isfunction(currentObject) or inspect.isroutine(currentObject):
                        addRow('class_method', mp, v, vv, currentObject, currentObject)
                    elif inspect.ismethod(currentObject):
                        addRow('class_method', mp, v, vv, currentObject, currentObject)
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
    recParseModule(inpath, basecomp)
    
    for prefix in modules:
        print 'NAMESPACE: ' + prefix
        addRow('namespace', '', '', prefix.replace('.', '::'), '', None)

def splitlinesstrip(s):
    return [line.strip() for line in s.splitlines() if line.strip()]

def parseRuby(filepaths, inpath, outpath):
    # ri -l -d <inpath>
    ripath = subprocess.check_output(['/usr/bin/which', 'ri']).strip()
    print 'RUBY IS AT ' + ripath
    # '/Users/alexgordon/.rvm/rubies/ruby-1.9.3-p194/bin/ri'
    output = subprocess.check_output([ripath, '-l', '-d', inpath, '--no-standard-docs'])
    classes = output.splitlines()
    
    SPLIT_REGEX = re.compile(r'^(=\s+[^\n]+|-{10,})\n', re.MULTILINE)
    DECL_REGEX = re.compile(r'<pre>(?:[a-zA-Z0-9_]+(?:\.|\:\:))?([a-zA-Z0-9_]+[!?]?(?:\([^\)\<\n]*\))?)(?:\s+(?:&gt;|=|\{)[^<\n]+)?</pre>')
    FULL_DECL_REGEX = re.compile(r'<pre>([^<]+)</pre>')
    
    for classname in classes:
        try:
            classoutput = subprocess.check_output([ripath, '-d', inpath, '--no-standard-docs', '-f', 'rdoc', classname])
            classhtmloutput = subprocess.check_output([ripath, '-d', inpath, '--no-standard-docs', '-f', 'html', classname])
        except Exception as e:
            print e
        
        superclass = ''        
        #print classoutput
        #print '$$$$$$$$$$$$$$$$$$$$$$$$$$$'
        #continue
        superclass = None
        instance_methods = []
        class_methods = []
        constants = []
        properties = []
        includes = []
        
        sections = SPLIT_REGEX.split(classoutput)
        mode = None
        for section in sections:
            section = section.strip()
            if not section or section.startswith('----------'):
                continue
            
            if section.startswith('= '):
                classdeclcomps = section[2:].split(' < ')
                if len(classdeclcomps) == 2:
                    superclass = classdeclcomps[1]
                    pass #print classdeclcomps
                elif section == '= Class methods:':
                    mode = 'class_method'
                elif section == '= Instance methods:':
                    mode = 'method'
                elif section == '= Constants:':
                    mode = 'constant'
                elif section == '= Attributes:':
                    mode = 'property'
                elif section == '= Includes:':
                    mode = 'includes'
                else:
                    #print section
                    mode = None
            elif mode:
                if mode == 'method':
                    instance_methods.extend(splitlinesstrip(section))
                elif mode == 'class_method':
                    class_methods.extend(splitlinesstrip(section))
                elif mode == 'constant':
                    #print 'CONSTANTS'
                    #print splitlinesstrip(section)
                    constants.extend(splitlinesstrip(section))
                elif mode == 'property':
                    #print 'PROPERTIES'
                    #print splitlinesstrip(section)
                    properties.extend(splitlinesstrip(section))
                elif mode == 'includes':
                    #print 'INCLUDES'
                    #print splitlinesstrip(section)
                    includes.extend(splitlinesstrip(section))
                    #print includes
        
        def insertmethod(methodname, queryidentifier, kind):
            methodoutput = subprocess.check_output([ripath, '-d', inpath, '--no-standard-docs', '-f', 'html', queryidentifier])
            
            module, _, classnamename = classname.rpartition('::')
            
            # module, parent, name, kind, defline, docs, linedecl
            defline = ''
            decls = DECL_REGEX.findall(methodoutput)
            if decls:
                defline = decls[0].strip()
                defline = defline.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'")
                defline = defline.replace('&amp;', '&')
            
            #if not defline:
                #print methodoutput
                #print ''
            
            if defline and not defline.endswith(')'):
                defline = defline + '()'
            
            fulldecls = FULL_DECL_REGEX.findall(methodoutput)
            fulldecl = ''
            if fulldecls:
                fulldecl = fulldecls[0].strip()
                fulldecl = fulldecl.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'")
                fulldecl = fulldecl.replace('&amp;', '&')
            
            
            #print '%s :: %s :: %s\n  %s\n^%s\n' % (module, classnamename, methodname, defline, fulldecl)
            #if not fulldecl:
            #    print methodoutput + '\n\n'
            original_namespace = ''
            addRowRaw(module, classnamename, methodname, original_namespace, kind, defline, methodoutput, fulldecl)
            
            #print methodoutput
            #print '????????'
            #methodoutput = subprocess.check_output([ripath, '-d', inpath, '--no-standard-docs', '-f', 'rdoc', classname + '#' + methodname])
            #print methodoutput
            #print '$@$@$@$@'
        
        def dealwithconstants(constantslist):
            for i, constant in enumerate(constantslist):
                if constant.endswith(':'):
                    constant = constant[:-1]
                    
                    explanation = constantslist[i + 1] if i < len(constantslist) else ''
                    module, _, classnamename = classname.rpartition('::')
                    original_namespace = ''
                    addRowRaw(module, classnamename, constant, original_namespace, 'constant', '', explanation, '')
            
        try:
            for methodname in instance_methods:
                insertmethod(methodname, classname + '#' + methodname, 'method')
            for methodname in class_methods:
                insertmethod(methodname, classname + '::' + methodname, 'class_method')
            
            dealwithconstants(constants)
            
            for attrname in properties:
                methodname = attrname.rpartition(' ')[2]
                insertmethod(methodname, classname + '#' + methodname, 'property')
            
        except Exception as e:
            print e
        
        module, _, classnamename = classname.rpartition('::')
        original_namespace = ''
        addRowRaw(module, '', classnamename, original_namespace,
          'class',
          '', classhtmloutput,
          'class ' + classnamename + (' < ' + superclass if superclass else ''))
        
        #print
        #print
        #print sections
    
    #print classes

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
        
        weighting REAL)""")
    c.execute("CREATE INDEX symbols_index ON symbols (name COLLATE NOCASE)")
    
    # Find all relevant files
    fileexts = extensionsForLanguage(language)
    filepaths = []
    '''
    for root, dirs, files in os.walk(inpath):
        for fp in files:
            ext = os.path.splitext(fp)[1].lower()
            fullpath = os.path.join(root, fp)
            if ext in fileexts:
                filepaths.append(fullpath)
    '''
    
    if language == 'py':
        # Do everything in a transaction
        with db:
            parsePython(filepaths, inpath, outpath)
    elif language == 'rb':
        parseRuby(filepaths, inpath, outpath)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
