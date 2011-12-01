import pyview.gui.objectmodel as objectmodel
import yaml

class Project(object):
  
  def __init__(self):
    self._tree = objectmodel.Folder("[project]")
    self._parameters = dict()
    self._filename = None
    self._lastState = self.saveToString()
    
  def parameters(self):
    return self._parameters
    
  def setParameters(self,parameters):
    self._parameters = parameters
    
  def tree(self):
    return self._tree
    
  def setTree(self,tree):
    self._tree = tree
    
  def setFilename(self,filename):
    self._filename = filename
    
  def filename(self):
    return self._filename
    
  def saveToFile(self,filename):
    string = self.saveToString()
    file = open(filename,"w")
    file.write(string)
    file.close()
    self.setFilename(filename)
    self._lastState = string
    
  def loadFromFile(self,filename):
    file = open(filename,"r")
    content =file.read()
    file.close()
    self.loadFromString(content)
    self.setFilename(filename)
    self._lastState = content
    
  def hasUnsavedChanges(self):
    if self._lastState != self.saveToString():
      return True
    return False
    
  def saveToString(self):
    converter = objectmodel.Converter()
    treedump = converter.dump(self._tree)
    return yaml.dump({'tree':treedump,'parameters':self._parameters})
    
  def loadFromString(self,string):
    params = yaml.load(string)
    converter = objectmodel.Converter()
    self._tree = converter.load(params["tree"])
    self._parameters = params["parameters"]