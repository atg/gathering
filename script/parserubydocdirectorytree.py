# From http://www.ruby-doc.org/downloads/

import os
root = 'data/ruby_1_9_3_stdlib/libdoc'
rs = os.listdir(root)

mappings = {}

banned = set(['Array', 'String', 'Enumerable', 'Object', 'Hash', 'Kernel', 'Class'])

def copyadd(arr, x):
    arr = arr[:]
    arr.append(x)
    return arr

def parse_lib(lib, libpath, libstack):
    if not os.path.isdir(libpath):
        return
    
    global mappings
    
    for childlib in os.listdir(libpath):
        subpath = os.path.join(libpath, childlib)
        if childlib == 'rdoc':
            # parse the lib
            #print '/'.join(libstack)
            childnames = []
            for filename in os.listdir(subpath):
                filepath = os.path.join(subpath, filename)
                if not filename.endswith('.html'):
                    continue
                
                filename, _, _ = filename.rpartition('.html')
                if filename == 'index' or filename.endswith('_rb'):
                    continue
                #if filename in banned:
                #    continue
                #print '  ' + filename
                childnames.append(filename)
            
            if childnames:
                mappings['/'.join(libstack)] = childnames
            
        else:
            parse_lib(childlib, subpath, copyadd(libstack, childlib))

for rootlibrary in rs:
    parse_lib(rootlibrary, os.path.join(root, rootlibrary), [rootlibrary])


from pprint import pprint
from json import dumps
print dumps(mappings)

# pprint(mappings)


