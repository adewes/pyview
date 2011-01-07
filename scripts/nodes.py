from latex import *
import string
import time

def sanitizeText(text):
  output = text
  output=re.sub('\\>','&gt;',re.sub('\\<','&lt;',output,reflags))
  return output

class HtmlNode:
  
  def __init__(self):
    pass
    
  def isBlock(self):
    return False
    
class HtmlInlineNode(HtmlNode):
  
  def __init__(self):
    HtmlNode.__init__(self)
    

class HtmlBlockNode(HtmlNode):

  def __init__(self):
    HtmlNode.__init__(self)
    
  def isBlock(self):
    return True

class Renderer:
  
  def __init__(self):
    self._text = '<p>'
    self._insideParagraph = True
    pass

  def closeParagraph(self):
    if self._insideParagraph == True:
      self._text += '</p>'
    self._insideParagraph = False
    
  def openParagraph(self):
    if self._insideParagraph == False:
      self._text+='<p>'
    self._insideParagraph = True
    
  def newParagraph(self):
    self.closeParagraph()
    self.openParagraph()
      
  def addInline(self,text):
    if text==None:
      return
    self.openParagraph()
    self._text+=text
  
  def addBlock(self,block):
    if block==None:
      return
    self.closeParagraph()
    self._text+=block
    
  def HTML(self):
    return self._text

class Node:

  def parser(self):
    return self._parser
    
  def setRenderer(self,renderer):
    self._renderer = renderer
    for child in self._children:
      child.setRenderer(renderer)
    
  def setParent(self,parent):
    self._parent = parent
    if parent != None:
      parent.addChild(self)
    
  def setParser(self,parser):
    self._parser = parser
  
  def isBlock(self):
    return self._isBlock
    
  def setBlock(self,block):
    self._isBlock=block
  
  def __init__(self,content):
    self._isBlock = False
    self._content = content
    self._parent = None
    self._parser = None
    self._children = []
    
  def parse(self):
    pass
  
  def addChild(self,child):
    self._children.append(child)  
  
  def render(self,format):
    return self._content

  def nodeInfo(self,level):
    return '[unknown]'
    
  def renderCode(self):
    return self._content
    
  def content(self):
    return self._content    
    
class MathNode(Node):

  def __init__(self,content,math,mathtype):
    Node.__init__(self,content)
    self._mathtype = mathtype
    self._math = math

  def nodeInfo(self):
    return '[math]'

  def render(self,format):
    if format == 'text/html':
      return self._mathtype+'<mathml>'+self._math+'</mathml>'  
  
class InlineCommandNode(Node):

  def __init__(self,content,command,arguments,optionals):
    Node.__init__(self,content)
    self._command = string.lower(command)
    self._arguments = arguments
    self._optionals = optionals
  
  def parse(self):
    try:
      attr = getattr(self,'parse'+self._command.capitalize())
      attr()
    except AttributeError:
      pass
    
  
  def _parseGeneralBlock(self):
    if len(self._arguments) > 0:
      self._innerLatex = Parser(self._arguments[0],self.parser(),self)
      self._innerLatex.parse()
    
  def parseChapter(self):
    self._parseGeneralBlock()
    
  def parseSection(self):
    self._parseGeneralBlock()
  
  def parseSubsection(self):
    self._parseGeneralBlock()
  
  def parseSubsubsection(self):
    self._parseGeneralBlock()
  
  def parseParagraph(self):
    self._parseGeneralBlock()
    
  def parseTextbf(self):
    self._parseGeneralBlock()

  def parseTextit(self):
    self._parseGeneralBlock()
  
  def renderTextbf(self):
    if len(self._arguments) > 0:
      self._renderer.addInline(self._renderHtmlBlock('strong',self._innerLatex.render()))

  def renderTextit(self):
    if len(self._arguments) > 0:
      self._renderer.addInline(self._renderHtmlBlock('i',self._innerLatex.render()))
  
  def renderSection(self):
    if len(self._arguments) > 0:
      self._renderer.addInline(self._renderHtmlBlock('h2',self._innerLatex.render()))

  def renderSubsection(self):
    if len(self._arguments) > 0:
      self._renderer.addBlock(self._renderHtmlBlock('h3',self._innerLatex.render()))
      
  def renderBigskip(self):
    return self._renderer.addInline('<br><br>')
    
  def renderSmallskip(self):
    return self._renderer.addInline('<br>')

  def renderSubsubsection(self):
    if len(self._arguments) > 0:
      return self._renderer.addBlock(self._renderHtmlBlock('h4',self._innerLatex.render()))

  def renderParagraph(self):
    if len(self._arguments) > 0:
      return self._renderer.addBlock(self._renderHtmlBlock('h5',self._innerLatex.render()))
   
  def renderChapter(self):
    if len(self._arguments) > 0:
      return self._renderer.addBlock(self._renderHtmlBlock('h1',self._innerLatex.render()))

  def _renderHtmlBlock(self,command,content):
    return self._renderer.addBlock('<'+command+'>'+content+'</'+command+'>')

  def nodeInfo(self):
    return '['+self._command+']'

  def render(self,format):
    if format == 'text/html':
      try:
        attr = getattr(self,'render'+self._command.capitalize())
        value = attr()
        if value != None:
          return value
        else:
          print 'Failed to render \"%s\" node.' % self._command
          return ''
      except AttributeError:
        return self._renderer.addInline('<%s>%s,%s</%s>' % (self._command,self._arguments,self._optionals,self._command))  

class BlockCommandNode(Node):

  def command(self):
    return self._command

  def __init__(self,content,command,arguments,optionals,block):
    Node.__init__(self,content)
    self._command = string.lower(command)
    self._arguments = arguments
    self._optionals = optionals
    self._block = block
    self._innerLatex = None
    
  def parse(self):
    try:
      fname = re.sub('\W','',self._command).capitalize()
      attr = getattr(self,'parse'+fname)
      attr()
    except AttributeError:
      self._parseInnerLatex()
  
  def _parseInnerLatex(self):
    self._innerLatex = Parser(self._block,self.parser(),self)
    self._innerLatex.parse()
    
  def nodeInfo(self):
    return '['+self._command+']'
            
  def parseFigure(self):
    self._parseInnerLatex()
    
  def parseEqnarray(self):
    pass
    
  def parseEquation(self):
    pass

  def parseTable(self):
    self._parseInnerLatex()
    
  def parseTabular(self):
    self._parseInnerLatex()
    
  def parseLongtable(self):
    self._parseInnerLatex()
    
  def parseVerbatim(self):
    pass
      
  def render(self,format):
    if format == 'text/html':
      try:
        attr = getattr(self,'render'+self._command.capitalize())
        return attr()
      except AttributeError:
        if self._innerLatex != None:
          return self._renderer.addBlock('<%s>%s,%s,%s</%s>' % (self._command,self._arguments,self._optionals,self._innerLatex.render(format),self._command))  
        else:
          return self._renderer.addBlock('<%s>%s,%s,%s</%s>' % (self._command,self._arguments,self._optionals,self._block,self._command))  
        
class TextNode(Node):

  def render(self,format):
    return self._renderer.addInline(sanitizeText(self._content))

  def nodeInfo(self):
    return '[textnode]'

