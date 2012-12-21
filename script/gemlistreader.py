import json
import pprint
import csv

with open('gemoutputspreadsheet.csv', 'wb') as csvfile:
    w = csv.writer(csvfile)
    

    p = '/Users/alexgordon/Desktop/gems.json'
    with open(p, 'r') as f:
        for line in f:
            
            if not line.startswith('{'):
                continue
            
            #print line.strip().rstrip(',')
            try:
                j = json.loads(line.strip().rstrip(',').rstrip(']'))
            except Exception as e:
                print line.strip().rstrip(',')
                break
            
            #pprint.pprint(j)
            w.writerow(map(str, [
                j['name'],
                j['version'],
                j['downloads'],
                j['version_downloads']
            ]))
        
    
    #j = json.load(f)
    