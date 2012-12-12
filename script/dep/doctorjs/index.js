var fs = require('fs'),
    tags = new (require('./jsctags/ctags/index').Tags)()

tags.scan(fs.readFileSync('./' + process.argv[2], 'utf8'))

console.log(tags)