import json
import subprocess
import urllib2

# Get a list of all gems
sep = ''
allgems = subprocess.check_output(['/usr/bin/env', 'gem', 'list', '--remote'])
#_, _, allgems = allgems.partition('*** REMOTE GEMS ***')
allgems = allgems.strip().splitlines()


print '['

for gem in allgems:
    print sep
    sep = ','
    
    try:
        gem, _, version = gem.partition(' ')
        #print gem
        #continue
        j = urllib2.urlopen('http://rubygems.org/api/v1/gems/%s.json' % gem).read()
        print j
        
        time.sleep(0.5)
    except Exception as e:
        pass

print ']'
