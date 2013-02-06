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


def handle_class(n, cl, ismodule, htmlifier, records)
  record = {}
  
  #puts ("CLASS " + cl.instance_variables.to_s)
  #puts "\n"
  #return
  
  
  record[:name] = n.rpartition("::")[2]
  record[:parents] = n.rpartition("::")[0]
  record[:fullname] = n
  record[:fullsignature] = cl.definition()
  #record[:filepath] = cl.
  
  if ismodule
    record[:type] = 'namespace'
  else
    record[:type] = 'class'
    record[:superclass] = cl.superclass
  end
  
  record[:html] = cl.comment.accept(htmlifier)
  records.push(record)
  cl.constants.each do |constant|
    
    constantrecord = {}
    constantrecord[:name] = constant.name
    constantrecord[:parents] = n
    constantrecord[:fullname] = n + "::" + constant.name
    constantrecord[:type] = 'constant'
    # constantrecord[:visibility] = constant.visibility
    if constant.value.kind_of?(String)
      constantrecord[:fullsignature] = n + " = " + constant.value
    end
    
    constantrecord[:html] = constant.comment.accept(htmlifier)
    records.push(constantrecord)
  end
end

names = store.modules()
names.each do |n|  
  #puts n
  if n == 'ActiveRecord::Base'
    next
  end
  
begin 
  cl = store.load_class(n)
  if cl.kind_of?(RDoc::NormalModule)
    handle_class(n, cl, true, htmler, records)
  elsif cl.kind_of?(RDoc::NormalClass)
    handle_class(n, cl, false, htmler, records)
  else
    #puts("????")
  end
rescue
end
end

#puts "DONE CLASSES"

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
  
  if isinstance
    record[:type] = 'method'
  else
    record[:type] = 'class_method'
  end
  
  record[:html] = comment.accept(htmlformatter)
  
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
  
  if readwrite.kind_of?(String)
    record[:canread] = readwrite.include?('R')
    record[:canwrite] = readwrite.include?('W')
  else
    record[:canread] = false
    record[:canwrite] = false
  end
  
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
    begin
      attrname = im.split(' ')[1]
      att = store.load_method(ims[0], '#' + attrname)
      handle_attr(att, records, ims[0], im, true, htmler)
    rescue
    end
  end
end

classmethods.each do |ims|
  ims[1].each do |im|
    begin
      meth = store.load_method(ims[0], im)
      handle_method(meth, records, ims[0], im, false, htmler)
    rescue
    end
  end
end

instancemethods.each do |ims|
  ims[1].each do |im|    
    begin
      meth = store.load_method(ims[0], '#' + im)
      handle_method(meth, records, ims[0], im, true, htmler)
    rescue
    end
  end
end

puts JSON.pretty_generate(records)
