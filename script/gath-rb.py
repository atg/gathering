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

stdlib19_modules = set(["Comparable", "Kernel", "Enumerable", "Errno", "FileTest", "File::Constants", "GC", "ObjectSpace", "GC::Profiler", "IO::WaitReadable", "IO::WaitWritable", "Marshal", "Math", "Process", "Process::UID", "Process::GID", "Process::Sys", "Signal"])

stdlib19_classes = set(["Array", "Bignum", "BasicObject", "Object", "Module", "Class", "Complex", "NilClass", "Numeric", "String", "Float", "Fiber", "FiberError", "Continuation", "Dir", "File", "Encoding", "Enumerator", "StopIteration", "Enumerator::Generator", "Enumerator::Yielder", "Exception", "SystemExit", "fatal", "SignalException", "Interrupt", "StandardError", "TypeError", "ArgumentError", "IndexError", "KeyError", "RangeError", "ScriptError", "SyntaxError", "LoadError", "NotImplementedError", "NameError", "NoMethodError", "RuntimeError", "SecurityError", "NoMemoryError", "EncodingError", "SystemCallError", "Encoding::CompatibilityError", "File::Stat", "IO", "Hash", "ENV", "IOError", "EOFError", "ARGF", "RubyVM", "RubyVM::InstructionSequence", "Math::DomainError", "ZeroDivisionError", "FloatDomainError", "Integer", "Fixnum", "Data", "TrueClass", "FalseClass", "Mutex", "Thread", "Proc", "LocalJumpError", "SystemStackError", "Method", "UnboundMethod", "Binding", "Process::Status", "Random", "Range", "Rational", "RegexpError", "Regexp", "MatchData", "Symbol", "Struct", "ThreadGroup", "ThreadError", "Time", "Encoding::UndefinedConversionError", "Encoding::InvalidByteSequenceError", "Encoding::ConverterNotFoundError", "Encoding::Converter", "RubyVM::Env"])

stdlib19 = stdlib19_modules | stdlib19_classes

with open('script/ruby1.9.3stdlib.json', 'r') as f:
    stdlib_mapping = json.load(f)
    for lib in stdlib_mapping.copy():
        stdlib_mapping[lib] = set(x for x in stdlib_mapping[lib] if x not in stdlib19)

def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)

def commonprefix(a, b):
    if not b: return a
    if not a: return b
    if a == b: return a
    _a = a.split('/')
    _b = b.split('/')
    maxworked = -1
    for i, (x, y) in enumerate(zip(_a, _b)):
        if x == y:
            maxworked = i
        else:
            break
    if maxworked == -1:
        return a
    return '/'.join(_a[0:maxworked+1])

def splitlinesstrip(s):
    return [line.strip() for line in s.splitlines() if line.strip()]

def combine(*vals):
    return '::'.join(x for x in vals if x)

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
    
    issystem = '.rvm/rubies/' in inpath
    
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
    createdb(db)
    
    print 'Begin'
    
    modules = []
    for record in j:
        if record['type'] == 'namespace':
            modules.append(record['fullname'])
    
    allowedkeys = {'fullsource', 'superclass', 'visibility', 'canread', 'canwrite', 'issingleton', 'libraryisstdlib', 'libraryname', 'librarypath'}
    invalidKernelNames = set(['j', 'jj', 'p', 'pp'])
    
    with db:
        for record in j:
            #print record['fullname']
            if record['type'] == 'method' or record['type'] == 'property':
                fullparents, _, name = record['fullname'].rpartition('#')
            else:
                fullparents, _, name = record['fullname'].rpartition('::')
            
            
            kind = record['type']
            
            if fullparents == 'Kernel'
                fullparents = ''
                if kind == 'method':
                    kind = 'function'
                if kind == 'class_method':
                    continue
                if name in invalidKernelNames:
                    continue
            
            if name.startswith('_'):
                continue
            if not name:
                continue
            
            if kind == 'method' or kind == 'class_method' or kind == 'function' or kind == 'property' or kind == 'class_property':
                if name[0].upper() == name[0]: # must be lowercase
                    continue
            else:
                if name[0].lower() == name[0]: # must be uppercase
                    continue
            
            if fullparents == '':
                namespace = ''
                parents = ''
            elif kind == 'method' or kind == 'class_method':
                namespace, _, parents = fullparents.rpartition('::')
            else:
                namespace = fullparents
            
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
            
            record['libraryisstdlib'] = False
            record['libraryname'] = ''
            record['librarypath'] = ''            
            
            if issystem:
                full_combined_name = combine(namespace, parents, name)
                if namespace in stdlib19 or combine(namespace, parents) in stdlib19 or full_combined_name in stdlib19:
                    record['libraryisstdlib'] = True
                else:
                    shouldbreak = False
                    for lib in stdlib_mapping:
                        if full_combined_name in stdlib_mapping[lib]:
                            record['libraryname'] = lib.partition('/')[0]
                            record['librarypath'] = commonprefix(lib, record['librarypath'])
                            #break
                        else:
                            for prefix in stdlib_mapping[lib]:
                                if full_combined_name.startswith(prefix + '::'):
                                    record['libraryname'] = lib.partition('/')[0]
                                    record['librarypath'] = commonprefix(lib, record['librarypath'])
                                    #shouldbreak = True
                                    #break
                        if shouldbreak:
                            break
                
            
            # TODO: CONSTANTS
            # html = 
            recordargs = { k: record[k] for k in record if k in allowedkeys }            
            
            addRowRaw(db, namespace, parents, name,
                      namespace, kind,
                      signature, record['html'], fullsignature,
                      **recordargs)
        
    # print modules
    with db:
        db.execute("ANALYZE")
    with db:
        db.execute("VACUUM")
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
