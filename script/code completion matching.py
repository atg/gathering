def both(a, b):
    return a and b
def neither(a, b):
    return (not a) and (not b)

def shouldMatchPair(full, fullQuery):
    modulePart, namePart = full
    queryModulePart, queryNamePart = fullQuery
    
    print '  (%s, %s) ~ (%s, %s)' % (modulePart, namePart, queryModulePart, queryNamePart)
    
    # If we have one module then we must have another
    if both(modulePart, queryModulePart):
        if both(namePart, queryNamePart):
            if modulePart != queryModulePart:
                return False
            
            return namePart.startswith(queryNamePart)
            
        elif neither(namePart, queryNamePart):
            return modulePart.startswith(queryModulePart)
            
        else:
            return False
        
    # Just names
    elif neither(modulePart, queryModulePart):
        return namePart.startswith(queryNamePart)
    
    return False

def buildName(fullName, isNamespace):
    # If fullName is a namespace then we have
    if isNamespace:
        return (fullName, '')
    else:
        module, _, name = fullName.rpartition('::')
        return (module, name)

def shouldMatch(imports, qualified_query, qualified_name, is_method, is_namespace):        
    queryComponents = qualified_query.split('::')
    query = queryComponents[-1]
    
    # If this is a method but not preceeded by a dot, then give up
    hasDot = len(queryComponents) > 1
    if is_method and not hasDot:
        return False
    
    full_name = buildName(qualified_name, is_namespace)
    
    for before, after, kind in imports:
        if kind == 2:
            fullQuery = before + '::' + qualified_query
            
            if shouldMatchPair(full_name, buildName(fullQuery, True)):
                return True
            if shouldMatchPair(full_name, buildName(fullQuery, False)):
                return True
        else:
            isStrictlyModule = kind == 1
            
            fullQuery = None
            if after == qualified_query:
                fullQuery = before
            elif qualified_query.startswith(after + "::"):
                withoutAfter = qualified_query[len(after):]
                fullQuery = before + withoutAfter
            elif after.startswith(qualified_query):
                withoutQuery = after[len(qualified_query):]
                withoutEnd = before[:-len(withoutQuery)]
                print '  %s' % ((qualified_query, withoutQuery, withoutEnd, before, after),)
                fullQuery = withoutEnd + withoutQuery
            
            print '  AFTER: %s ~ %s' % (after, qualified_query)
            
            if fullQuery:
                if shouldMatchPair(full_name, buildName(fullQuery, True)):
                    return True
                
                builtName = buildName(fullQuery, False)
                print 'FN1: %s' % [full_name]
                print 'BN1: %s' % [builtName]
                print 'isStrictlyModule %d' % isStrictlyModule
                print 'is_namespace %d' % is_namespace
                print '%s -> %s' % (before, after)
                
                if not (isStrictlyModule and (not is_namespace) and qualified_name == before):
                    
                
                #if is_namespace or not isStrictlyModule:
                    if shouldMatchPair(full_name, builtName):
                        return True
    
    return False


shouldBeTrue = [
(lambda: shouldMatch(
    [('django::db::models', 'models', 0)],
    'models::Mod',
    'django::db::models::Model', False, False)),

(lambda: shouldMatch(
    [('django::db::models::render', 'render', 0)],
    'rend',
    'django::db::models::render', False, False)),

(lambda: shouldMatch(
    [('django::db::models', 'django::db::models', 1)],
    'django::db::mod',
    'django::db::models', False, True)),

(lambda: shouldMatch(
    [('django::db::models::render', 'showaddywaddy::render', 0)],
    'showaddywaddy::rend',
    'django::db::models::render', False, False)),

(lambda: shouldMatch(
    [('django::db::models::render', 'showaddywaddy::render', 0)],
    'showaddywaddy',
    'django::db::models::render', False, False)),

    (lambda: shouldMatch(
        [('subprocess', 'subprocess', 1)],
        'subprocess::che',
        'subprocess::check_output', False, False)),

(lambda: shouldMatch(
    [('django::db::models', 'sudo::make::me::a::models', 1)],
    'sudo::make::me::a::mod',
    'django::db::models', False, True)),

(lambda: shouldMatch(
    [('django::db', 'django::db', 1)],
    'django::db::mod',
    'django::db::models', False, True)),


(lambda: shouldMatch(
    [('django', 'django', 1)],
    'django::db::mod',
    'django::db::models', False, True)),

(lambda: shouldMatch(
    [('django', 'rails', 1)],
    'rails::db::mod',
    'django::db::models', False, True)),

(lambda: shouldMatch(
    [('django::db', 'rails::bananas', 1)],
    'rails::bananas::mod',
    'django::db::models', False, True)),

(lambda: shouldMatch(
    [('django::db::models', '', 2)],
    'Mod', 'django::db::models::Model', False, False)),
]


shouldBeFalse = [

(lambda: shouldMatch(
    [('django::db::models', 'sudo::make::me::a::models', 1)],
    'sudo::make::me::a::mod',
    'django::db::models', False, False)),

(lambda: shouldMatch(
    [('django::db', 'django::db', 1)],
    'django::db::mod',
    'django::db::models', False, False)),

(lambda: shouldMatch(
    [('django', 'django', 1)],
    'django::db::mod',
    'django::db::models', False, False)),

(lambda: shouldMatch(
    [('django', 'rails', 1)],
    'rails::db::mod',
    'django::db::models', False, False)),

(lambda: shouldMatch(
    [('django::db::models', 'rails::bananas::models', 1)],
    'rails::bananas::mod',
    'django::db::models', False, False)),
]



for lam in shouldBeTrue:
    result = lam()
    if result:
        print '  ok'
    else:
        print 'WAS FALSE!!!!'
    print '  ==========='

for lam in shouldBeFalse:
    result = lam()
    if not result:
        print '  ok2'
    else:
        print 'WAS TRUE!!!!'
    print '  ==========='


'''
imports = [('django::db::models', 'models', 0)]
print 'Result: %s' % shouldMatch(imports, 'models::Mod', 'django::db::models::Model', False, False)

print '---'

imports = [('django::db::models::render', 'render', 0)]
print 'Result: %s' % shouldMatch(imports, 'rend', 'django::db::models::render', False, False)

print '---'

imports = [('django::db::models', 'django::db::models', 1)]
print 'Result: %s' % shouldMatch(imports, 'django::db::mod', 'django::db::models', False, True)

print '---'


imports = [('django::db', 'django::db', 1)]
print 'Result: %s' % shouldMatch(imports, 'django::db::mod', 'django::db::models', False, True)

print '---'

imports = [('django', 'django', 1)]
print 'Result: %s' % shouldMatch(imports, 'django::db::mod', 'django::db::models', False, True)

print '---'

imports = [('django', 'rails', 1)]
print 'Result: %s' % shouldMatch(imports, 'rails::db::mod', 'django::db::models', False, True)

print '---'

imports = [('django::db::models', '', 2)]
print 'Result: %s' % shouldMatch(imports, 'Mod', 'django::db::models::Model', False, False)

'''