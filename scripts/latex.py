import re 
import string

class Command:
  pass
  
class TextBlock:
  pass
  
class MathBlock:
  pass
  
rules = dict()

rules['no_escape_char'] = r'(?<![^\\]\\)'
rules['escape_char'] = r'[^\\]\\'
rules['text'] = r'[^\\\$\{]+'
rules['command'] = r'(\\[\w\*]+|\\[^\w])'
rules['block'] = rules['no_escape_char']+r'(\{)'
rules['math'] = rules['no_escape_char']+r'\$'

for rule in rules.keys():
  print 'rule[%s] = %s' % (rule,rules[rule])

reflags = re.DOTALL |re.MULTILINE | re.IGNORECASE


def smart_truncate(content, length=100, suffix='...'):
    if len(content) <= length+5:
        return content
    else:
        return content[:length/2]+'...'+content[len(content)-length/2:len(content)]
        
class Parser:

  def addNode(self,node):
    node.setParent(self._parentNode)
    node.setParser(self)
    node.parse()
    self._nodes.append(node)

  def flushNodeQueue(self):
    for node in self._nodeQueue:
      node.parse()
      self._nodes.append(node)
    
  def render(self,format = 'text/html'):
    output = ''
    renderer = Renderer()
    for node in self._nodes:
      node.setRenderer(renderer)
      node.render(format)
    return renderer.HTML()
    
  def parseNodeInfo(self,nodes,level):
    nodeinfos = ''
    for node in nodes:
      nodeinfos = nodeinfos + ('\t'*level)+node.nodeInfo()+'\n'
      nodeinfos = nodeinfos + self.parseNodeInfo(node._children,level+1)
    return nodeinfos
    
  def documentStructure(self):
    return self.parseNodeInfo(self._nodes,0)

  def renderCode(self):
    output = ''
    for node in self._nodes:
      output += node.renderCode()
    return output
  
  def __init__(self,text,parentParser = None, parentNode = None):
    self._text = text
    self._nodes = []
    self._nodeQueue = []
    self._parentParser = parentParser
    self._parentNode = parentNode
  
  def parseError(self,message,parsedText = ''):
    if self._parentParser != None:
      self._parentParser.parseError(message,self._parsedText+parsedText)  
    else:
      parsedText = self._parsedText +parsedText
      errorText = ''
      forward_length = 0
      backward_length = 0 
      lineNumbers = re.findall('\\n(.*)',parsedText,re.M)
      while len(re.findall('\\n',errorText,re.M)) < 1 and len(errorText) < 400:    
        forward_length += 1
        errorText = self._text[len(parsedText)-forward_length:len(parsedText)]
      while len(re.findall('\\n',errorText,re.M)) < 2 and len(errorText) < 400:    
        backward_length += 1
        errorText = self._text[len(parsedText)-forward_length:len(parsedText)+backward_length]
      numberedErrorText =''
      linenumber = len(lineNumbers)
      for line in errorText.split('\n'):
          numberedErrorText+="%d\t:%s\n" % (linenumber,line)
          linenumber+=1
      testfile = open('test.dat','w')
      testfile.write(parsedText)
      testfile.close()
      print "Line %d, pos. %d: %s" % (1+len(lineNumbers),len(lineNumbers[len(lineNumbers)-1]),message)
      print numberedErrorText
      
  def movePointer(self,remaining):
    self._parsedText += self.pointer[0:len(self.pointer)-len(remaining)]
    self.pointer = remaining
    
      
  def parse(self):
    self.pointer = self._text
    self._parsedText = ''

    while self.pointer != '':
#      print "%d remaining." % len(self.pointer)
      if self.check_for_text(self.pointer):
#        print "Parsing text"
        self.parse_text(self.pointer)
#        print "Done"
      elif self.check_for_math(self.pointer):
        self.parse_math(self.pointer)

      elif self.check_for_block(self.pointer,'\\{','\\}'):
        self.parse_block_node(self.pointer)

      elif self.check_for_command(self.pointer):
        self.parse_command(self.pointer)

      else:
        break

    return self
  
        
  def check_for_math(self,pointer):
    if re.match(rules['math'],pointer,reflags)!= None:
      return True
    return False
      
  
  def check_for_text(self,pointer):
    result = re.match(rules['text'],pointer,reflags)
    if result == None:
        return False
    return True

  def parse_block_node(self,pointer):
    (block,remaining) = self.parse_block(pointer,'\\{','\\}')   
    node = BlockCommandNode(block,'block',[],[],block[1:])
    self.addNode(node)
    self.movePointer(remaining)
    return remaining
            
  def check_for_command(self,pointer):
    result = re.match(rules['command'],pointer,reflags)
    if result != None:
      return True
    return False
  
  def parse_math(self,pointer):
    result = None
    if re.match('(?<!\\\\)\\$\\$',pointer,reflags) != None:
      result = self.parse_block(pointer,'\\$\\$','\\$\\$')
      if result == None:
        return ''
    elif re.match('(?<!\\\\)\\$',pointer,reflags) != None:
      result = self.parse_block(pointer,'\\$','\\$')
      if result == None:
        return ''
    (mathblock,remaining) = result
    mathtype = 'inline'
    if re.match('^\\$\\$',mathblock,reflags) != None:
      mathtype = 'block'
    math = re.sub('\\$\\$$|\\$$','',re.sub('^\\$\\$|^\\$','',mathblock))

    node = MathNode(mathblock,math,mathtype)

    self.addNode(node)
    return self.movePointer(remaining)
  
  def parse_text(self,pointer):
    match = re.match(rules['text'],pointer,reflags)
    if match == None:
      self.parseError("Parsing error:"+pointer[:100])
      self.movePointer('')
      return

    text = match.string[match.start(0):match.end(0)]    
    node = TextNode(text)
    self.addNode(node)
    
    self.movePointer(match.string[match.end(0):])
  
  
  def parse_arguments(self,pointer):
    arguments = []
    optionals = []
    remaining = pointer
    parsed_string = ''
    hasOptionals = self.check_for_block(remaining,'\[','\]')
    hasArguments = self.check_for_block(remaining,'\{','\}')
    while hasOptionals or hasArguments:
      if hasOptionals:
        (optional,remaining) = self.parse_block(remaining,'\[','\]')
        optionals.append(optional[1:len(optional)-1])
        parsed_string=parsed_string + optional
      elif hasArguments:
        (argument,remaining) = self.parse_block(remaining,'\{','\}')
        arguments.append(argument[1:len(argument)-1])
        parsed_string=parsed_string + argument
      hasOptionals = self.check_for_block(remaining,'\[','\]')
      hasArguments = self.check_for_block(remaining,'\{','\}')
        
#    print "Returning %d arguments and %d optionals." % (len(arguments),len(optionals))
    return (arguments,optionals,remaining,parsed_string)
  
  def parse_command(self,pointer):
    result = self.parse_latex_command(pointer)
    if result == None:
      self.parseError("Parsing error!")
      return self.movePointer('')
    (command,remaining) = result
    if string.lower(command) == '\\begin':
      #We parse a begin/end block
      result = self.parse_block(remaining,'\{','\}')
      if result == None:
        self.movePointer('')
        self.parseError('EOF while scanning for end of block')
        return
      (inner_command,remaining_inner)= result
      self.movePointer(remaining_inner)
      inner_command = inner_command[1:len(inner_command)-1]
      command_block = self.parse_block(command+remaining,'\\\\begin\{'+re.escape(inner_command)+'\}','\\\\end\{'+re.escape(inner_command)+'\}')
      if command_block == None:
       self.movePointer(remaining_inner)
       self.parseError("EOF while scanning for end of block command.")
       return
      (full_block,remaining) = command_block
      block = re.sub('\\\\end\{'+inner_command+'\}$','',re.sub('^\\\\begin\{'+inner_command+'\}','',full_block))
      (arguments,optionals,block,parsed_args) = self.parse_arguments(block)
    
      node = BlockCommandNode(full_block,inner_command,arguments,optionals,block)
      self.addNode(node)
      return self.movePointer(remaining)
    else:
      (arguments,optionals,remaining,parsed_args) = self.parse_arguments(remaining)
      node = InlineCommandNode(command+parsed_args,command[1:],arguments,optionals)
      self.addNode(node)
      return self.movePointer(remaining)
    return ''
            
  def parse_latex_command(self,pointer):
      match = re.match(rules['command'],pointer,reflags)
      if match == None:
        return None
      match_string = match.string[match.start(0):match.end(0)] 
      remaining_string = match.string[match.end(0):]
      return (match_string,remaining_string) 

  def check_for_block(self,pointer,opening_tag,closing_tag):
    match = re.match(r'('+rules['no_escape_char']+opening_tag+r'.*?'+rules['no_escape_char']+closing_tag+')',pointer,reflags)
    if match != None:
      return True
    return False    
    
  def parse_block(self,pointer,opening_tag,closing_tag):
      firstmatch = re.match(r'('+rules['no_escape_char']+opening_tag+r'.*?'+rules['no_escape_char']+closing_tag+')',pointer,reflags)
      if firstmatch == None:
        return None
      block_string = firstmatch.string[firstmatch.start(0):firstmatch.end(0)]
      remaining_string = firstmatch.string[firstmatch.end(0):]
      opening_tags = len(re.findall('('+rules['no_escape_char']+opening_tag+')',block_string,reflags)) 
      closing_tags = len(re.findall('('+rules['no_escape_char']+closing_tag+')',block_string,reflags))
      while opening_tags != closing_tags:
        additional = re.match('('+'.*?'+rules['no_escape_char']+closing_tag+')',remaining_string,reflags)
        if additional == None:
          self.parseError("EOF while scanning for end of %s...%s block!" % (opening_tag,closing_tag))
          return (block_string,remaining_string)
        block_string = block_string + additional.string[additional.start(0):additional.end(0)]
        opening_tags = len(re.findall('('+rules['no_escape_char']+opening_tag+')',block_string,reflags)) 
        closing_tags = len(re.findall('('+rules['no_escape_char']+closing_tag+')',block_string,reflags))
        remaining_string = additional.string[additional.end(0):]
        remaining_string = additional.string[additional.end(0):]
  #      print "New block string:%s" % block_string
      return (block_string,remaining_string)

from nodes import *
  