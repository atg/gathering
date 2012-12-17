require 'rdoc'
require 'rdoc/ri'
require 'rdoc/markup'
require 'rdoc/markup/formatter'
require 'json'

records = []

htmler = RDoc::Markup::ToHtml.new()

#puts(ARGV[0])
store = RDoc::RI::Store.new(ARGV[0])
store.dry_run = true
store.load_cache()

names = store.modules()
names.each do |n|  
  cl = store.load_class(n)
  if cl.kind_of?(RDoc::NormalModule)
    #puts('[m]: ' + n)
    #puts('~~ ' + cl.to_s)
    #puts('   ' + cl.definition())
    
    record = {}
    record[:name] = n.rpartition("::")[2]
    record[:parents] = n.rpartition("::")[0]
    record[:fullname] = n
    record[:fullsignature] = cl.definition()
    record[:type] = 'namespace'
    
    #driver = RDoc::RI::Driver.new()
    #moduledoc = driver.display_class(cl)
    record[:html] = cl.comment.accept(htmler)
    records.push(record)
    
  elsif cl.kind_of?(RDoc::NormalClass)
    #puts('[c]: ' + n)
    #puts('~~ ' + cl.to_s)
    #puts('   ' + cl.definition())
    
    record = {}
    record[:name] = n.rpartition("::")[2]
    record[:parents] = n.rpartition("::")[0]
    record[:fullname] = n
    record[:fullsignature] = cl.definition()
    record[:type] = 'class'
    record[:superclass] = cl.superclass
    record[:html] = cl.comment.accept(htmler)
    records.push(record)
    
  else
    #puts("????")
  end
end

attrs = store.attributes()
classmethods = store.class_methods()
instancemethods = store.instance_methods()

def handle_method(meth, records, parents, name, isinstance, htmlformatter)
  record = { }
  
  dump = meth.marshal_dump
  # [   MARSHAL_VERSION,
  #     @name,
  #     full_name,
  #     @singleton,
  #     @visibility,
  #     parse(@comment),
  #     @call_seq,
  #     @block_params,
  #     aliases,
  #     @params,
  #     @file.absolute_name,
  #   ]
    
  methname = dump[1]
  fullname = dump[2]
  singleton = dump[3]
  visibility = dump[4]
  comment = dump[5]
  callseq = dump[6]
  blockparams = dump[7]
  aliases = dump[8]
  params = dump[9]
  filepath = dump[10]
  
  record[:name] = methname
  record[:parents] = parents
  record[:fullname] = fullname
  record[:filepath] = filepath
  record[:visibility] = visibility
  record[:fullsignature] = methname + meth.param_seq.to_s
  record[:minisignature] = methname + meth.params.to_s
  record[:issingleton] = meth.singleton
  #record[:marshal_dump] = meth.callseq
  if isinstance
    record[:type] = 'method'
  else
    record[:type] = 'class_method'
  end
  
  record[:html] = comment.accept(htmlformatter)
  
  #puts '<<<<\n' + html.to_s + '\n>>>>'
  #puts comment.parts.to_s
  #html = htmler.convert(meth.comment.text)
  #puts html
  #puts(meth.markup_code())
  #puts('   ' + comment.parts.to_s)
  
  #puts('   ' + meth.marshal_dump.to_s)
  #puts('   ' + meth.params.to_s)
  #puts('   ' + meth.param_seq.to_s)
  
  records.push(record)
end

def handle_attr(att, records, parents, name, isinstance, htmlformatter)
  record = { }
  
  dump = att.marshal_dump
  # [ MARSHAL_VERSION,
  #       @name,
  #       full_name,
  #       @rw,
  #       @visibility,
  #       parse(@comment),
  #       singleton,
  #       @file.absolute_name,
  #     ]
    
  attname = dump[1]
  fullname = dump[2]
  readwrite = dump[3]
  visibility = dump[4]
  comment = dump[5]
  singleton = dump[6]
  filepath = dump[7]
  
  record[:name] = attname
  record[:parents] = parents
  record[:fullname] = fullname
  record[:filepath] = filepath
  record[:visibility] = visibility
  #puts readwrite
  record[:canread] = readwrite.include?('R')
  record[:canwrite] = readwrite.include?('W')
  
  record[:fullsignature] = name
  #record[:minisignature] = attname + att.params.to_s
  record[:issingleton] = singleton
  
  if isinstance
    record[:type] = 'property'
  else
    record[:type] = 'class_property'
  end
  
  record[:html] = comment.accept(htmlformatter)
  
  records.push(record)
end


attrs.each do |ims|
  ims[1].each do |im|
    #puts('  [ a] ' + ims[0] + ' --- ' + im)
    attrname = im.split(' ')[1]
    att = store.load_method(ims[0], '#' + attrname)
    #puts(att.class.name)
    #puts(att.marshal_dump.to_s)
    handle_attr(att, records, ims[0], im, true, htmler)
  end
end

classmethods.each do |ims|
  ims[1].each do |im|
    # puts('  [cm] ' + ims[0] + ' --- ' + im)
    meth = store.load_method(ims[0], im)
    handle_method(meth, records, ims[0], im, false, htmler)
  end
end

instancemethods.each do |ims|
  ims[1].each do |im|    
    # puts('  [im] ' + ims[0] + ' --- ' + im)
    meth = store.load_method(ims[0], '#' + im)
    handle_method(meth, records, ims[0], im, true, htmler)
  end
end

puts JSON.pretty_generate(records)
