def addRowRaw(db, module, parent, name, original_namespace, kind, defline, docs, linedecl, **others):
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    print '%s, %s  [%s] // %d' % (kind, qualname, defline, len(docs))
    #print docs

    fullsource = others['fullsource'] if 'fullsource' in others else ''
    superclass = others['superclass'] if 'superclass' in others else ''
    
    visibility = others['visibility'] if 'visibility' in others else ''
    canread = others['canread'] if 'canread' in others else None
    canwrite = others['canwrite'] if 'canwrite' in others else None
    issingleton = others['issingleton'] if 'issingleton' in others else None

    librarypath = others['librarypath'] if 'librarypath' in others else ''
    libraryname = others['libraryname'] if 'libraryname' in others else ''
    libraryisstdlib = others['libraryisstdlib'] if 'libraryisstdlib' in others else False
    
    c = db.cursor()
    c.execute("""INSERT INTO symbols (
        namespace, parents, name, original_namespace,
        type_code, declaration, documentation, sourcedecl,
        fullsource, superclass,
        visibility, canread, canwrite, issingleton,
        librarypath, libraryname, libraryisstdlib) VALUES (
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?)""", (
        module, parent, name, original_namespace,
        kind, defline, removeNonAscii(docs), linedecl,
        fullsource, superclass,
        visibility, canread, canwrite, issingleton,
        librarypath, libraryname, libraryisstdlib))


'''
def addRowRaw(module, parent, name, original_namespace, kind, defline, docs, linedecl, **others):
    qualname = '::'.join(filter(lambda x: bool(x), [module, parent, name]))
    print '%s, %s  [%s] // %d' % (kind, qualname, defline, len(docs))
    #print docs

    fullsource = others['fullsource'] if 'fullsource' in others else ''
    superclass = others['superclass'] if 'superclass' in others else ''
    isDocumented = others['isDocumented'] if 'isDocumented' in others else False

    c = db.cursor()
    c.execute("INSERT INTO symbols (namespace, parents, name, original_namespace, type_code, declaration, documentation, sourcedecl, fullsource, superclass, isDocumented) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (module, parent, name, original_namespace, kind, defline, removeNonAscii(docs), linedecl, removeNonAscii(fullsource), superclass, isDocumented))
'''

def createdb(db):
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
        
        librarypath TEXT, libraryname TEXT, libraryisstdlib BOOLEAN,
        
        weighting REAL)""")
    c.execute("CREATE INDEX symbols_index ON symbols (name COLLATE NOCASE)")
    c.execute("CREATE INDEX symbols_typecode_index ON symbols (type_code, name COLLATE NOCASE)")
    
    
    
    '''
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
    c.execute("CREATE INDEX symbols_typecode_index ON symbols (type_code, name COLLATE NOCASE)")
    '''

