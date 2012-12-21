import os, subprocess, re

VERSION = 1


def handlePath(p, p2, isFile):
    name, _, version = os.path.basename(p2).rpartition('-')
    if not name:
        return
    parent = os.path.basename(os.path.dirname(p))
    return ((parent, name, version, p, isFile))

def scanPaths():
    for root, dirs, files in os.walk('libs'):
        if len(root.split('/')) >= 3:
            continue
        
        for f in files:
            if f == '.DS_Store':
                continue
            p = os.path.join(root, f)
            p2, ext = os.path.splitext(p)
            if not ext:
                continue
            t = handlePath(p, p2, True)
            if t:
                yield t
        for d in dirs:
            p = os.path.join(root, d)
            t = handlePath(p, p, False)
            if t:
                yield t

RUBY_COMPONENT_REGEX = re.compile(r'/doc/([^/]+)\-([^/]+)/ri')

def main():    
    # Look through the libraries
    for parent, name, version, path, isFile in scanPaths():
        path = os.path.abspath(path)
        
        print (parent, name, version, path, isFile)
        
        # See if we have indexed this particular one
        outpath = 'databases/v%d/%s--%s-%s.db' % (VERSION, parent, name, version)
        outpath = os.path.abspath(outpath)
        print '  ' + outpath
        
        # Ignore it if it exists
        if os.path.exists(outpath):
            continue
        
        if parent == 'php':
            pass #subprocess.check_output(['script/gath-php.py', 'php', path, outpath])
        elif parent == 'js':
            pass #subprocess.check_call(['/usr/bin/python', 'gath-js.py', 'js', path, outpath], cwd='script')
        elif parent == 'python':
            print ['/usr/bin/python', 'thegatherer.py', 'py', path + '/' + name, outpath]
            subprocess.check_call(['/usr/bin/python', 'thegatherer.py', 'py', path + '/' + name, outpath], cwd='script')
        elif parent == 'ruby':
            pass #subprocess.check_output(['script/thegatherer.py', 'rb', path, outpath])
        else:
            continue
    
    # Look through ruby
    # ri --list-doc-dirs
    # print subprocess.check_output(['/usr/bin/which', 'ri'])
    
    rubypaths = subprocess.check_output(['/usr/bin/env', 'ri', '--list-doc-dirs']).splitlines()
    for rubypath in rubypaths:
        if not rubypath.endswith('/ri'):
            continue
        
        outcomponents = RUBY_COMPONENT_REGEX.findall(rubypath)
        if not outcomponents:
            continue
        
        outpath = 'databases/v%d/%s--%s-%s.db' % (VERSION, 'ruby', outcomponents[0][0], outcomponents[0][1])
        outpath = os.path.abspath(outpath)
        # Ignore it if it exists
        if os.path.exists(outpath):
            continue
        
        print rubypath
        print '  ' + outpath
        
        subprocess.check_call(['/usr/bin/python', 'script/gath-rb.py', 'rb', rubypath, outpath])
        # /Users/alexgordon/.rvm/gems/ruby-1.9.3-p194/doc/ruport-1.6.3/ri
        # /Users/alexgordon/.rvm/gems/ruby-1.9.3-p194@global/doc/rvm-1.11.3.5/ri
        

if __name__ == '__main__':
    main()
