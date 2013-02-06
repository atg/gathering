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

def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)



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
                    break
                elif parents == mod:
                    namespace = mod
                    newparents = ''
                    break
            parents = newparents
        
            #print '  ' + str((namespace, parents, name))
            #pprint(record)
            
            kind = record['type']
        
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
            
            if namespace in stdlib19 or combine(namespace, parents) in stdlib19 or combine(namespace, parents, name) in stdlib19:
                record['libraryisstdlib'] = True
                record['libraryname'] = ''
                record['librarypath'] = ''
            
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
