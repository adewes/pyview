from ctypes import *
from numpy import *
from scipy import *
import yaml
import StringIO
import os
import os.path
import pickle
import sys
import copy
import time
import weakref
import re
import string

from pyview.lib.patterns import Subject,Observer,Reloadable

class ChildItem:
  
  def __init__(self,datacube,attributes):
    self._datacube = datacube
    self._attributes = attributes

  def datacube(self):
    return self._datacube
    
  def attributes(self):
    return self._attributes
    
#This is a hirarchical data storage class. A datacube stores a 2-dimensional array of values. Each array len(self._table[self._index,:])) is identified by a name. In addition, you can add one or more "child datacubes" to each row of the array, thus creating a multidimensional data model.
class Datacube(Subject,Observer,Reloadable):
  """
  This is a hirarchical data storage class. 
  
  A datacube stores a 2-dimensional array of values. Each array len(self._table[self._index,:])) is identified by a name. In addition, you can add one or more "child datacubes" to each row of the array, thus creating a multidimensional data model.
    
  """
  defaults = dict()

  version = "0.2"
  
  def __init__(self,*args,**kwargs):
    Subject.__init__(self)
    Observer.__init__(self)
    Reloadable.__init__(self)
    self.initialize(*args,**kwargs)
    
  def initialize(self,name = "datacube",description = "",filename = None,dtype = float64,defaults = None):
    
    """
    Initializes the data cube.
    """
    
    self._meta = dict()
    if defaults == None:
      defaults = Datacube.defaults
    self._meta["defaults"] = defaults
    self._meta["filename"] = filename
    self._meta["name"] = name
    self._meta["fieldNames"] = []
    self._meta["description"] = description
    self._meta["fieldMap"] = dict()
    self._meta["parameters"] = dict()
    self._meta["index"] = 0
    self._meta["tags"] = ""
    self._meta["length"] = 0
    self._meta["dataType"] = dtype
    self._meta["modificationTime"] = time.asctime()
    self._meta["creationTime"] = time.asctime()
    
    self._children = []
    self._parameters = dict()
    self._table = None
    self._parent = None
    
    self._changed = False
    self._unsaved = True
    self._adjustTable()
    
  def parent(self):
    if self._parent == None:
      return None
    return self._parent
    
  def setParent(self,parent):
    
    """
    Sets the parent of the data cube to *parent*.
    """
  
    if parent != None:
      self._parent = parent
    
  def index(self):
  
    """
    Returns the current row index.
    """
  
    return self._meta["index"]
    
  def parameters(self):
    """
    Returns the parameters of the data cube. The parameter dictionary is saved along with the datacube.
    """
    return self._parameters
    
  def setParameters(self,params):
    """
    Sets the parameters of the datacube to *params*
    """
    self._parameters = params
    self.setModified()
    self.notify("parameters",params)
    
    
  def setFilename(self,filename):
    """
    Sets the filename of the datacube to *filename*.
    """
    self._meta["filename"] = os.path.realpath(filename)
    self.setModified()
    self.notify("filename",filename)
    
  def filename(self):
    """
    Returns the filename of the datacube.
    """
    return self._meta["filename"]
      
  def tags(self):
    """
    Returns the tags of the datacube.
    """
    return self._meta["tags"]
    
  def description(self):
    """
    Returns the description of the datacube
    """
    return self._meta["description"]
    
  def setTags(self,tags):
    """
    Sets the tags of the datacube
    """
    self._meta["tags"] = str(tags)
    self.setModified()
    self.notify("tags",tags)
    
  def setDescription(self,description):
    """
    Sets the description of the datacube
    """
    self._meta["description"] = str(description)
    self.setModified()
    self.notify("description",description)
  
  def structure(self,tabs = ""):
    """
    Returns a string describing the structure of the datacube
    """
    string = tabs+"cube(%d,%d)" % (self._meta["length"],len(self._meta["fieldNames"]))+"\n"
    for item in self._children:
      child = item.datacube()
      attributes = item.attributes()
      parts = []
      for key in attributes:
        parts.append((" %s = " % str(key))+str(attributes[key]))
      string+=", ".join(parts)+":\n"
      string+=child.structure(tabs+"\t")
    return string
   
  def columns(self,names):
    """
    Returns a table containing a set of given columns
    """
    indices = []
    for i in range(0,len(names)):
      indices.append(self._meta["fieldMap"][names[i]])
    if len(indices) == 1:
      return self.table()[:,indices[0]]
    else:
      return self.table()[:,indices]
    
  def columnName(self,index):
    for key in self._meta["fieldMap"].keys():
      if self._meta["fieldMap"][key] == index:
        return key
    return None
    
  def column(self,name):
    """
    Returns a given column of the datacube
    """
    if name in self._meta["fieldMap"]:
      return self._table[:self._meta["length"],self._meta["fieldMap"][name]]
    return None

  def removeColumn(self,name):
    if not name in self._meta["fieldNames"]:
      return

    oldTable = self.table()
    col = self._meta["fieldMap"][name]

    del self._meta["fieldNames"][self._meta["fieldNames"].index(name)]
    del self._meta["fieldMap"][name]

    self._table = None
    self._adjustTable()

    mlen = min(len(self._table),len(oldTable))
    self._table[:mlen,:col] = oldTable[:mlen,:col]
    self._table[:mlen,col:] = oldTable[:mlen,col+1:]
    self.notify("commit",self._meta["index"])
    
  def removeColumns(self,names):
    for name in names:
      self.removeColumn(name)

  def _adjustTable(self):
    """
    Resizes the table, if necessary
    """
    if self._table == None: 
      self._table=zeros((self._meta["length"]+1,len(self._meta["fieldNames"])),dtype = self._meta["dataType"])
    elif shape(self._table)[1] < len(self._meta["fieldNames"]):
      newarray = zeros((len(self._table),len(self._meta["fieldNames"])),dtype = self._meta["dataType"])
      newarray[:,:len(self._table[0,:])]=self._table
      self._table = newarray
      self.notify("names",self._meta["fieldNames"])
    for i in range(0,len(self._meta["fieldNames"])):
      self._meta["fieldMap"][self._meta["fieldNames"][i]] = i
                
  def clear(self):
    """
    Resets the datacube to its initial state
    """
    self.initialize()
    
  def table(self):
    """
    Returns the data table
    """
    return self._table[:self._meta["length"],:]
    
  def setIndex(self,index):
    """
    Synonym for goTo
    """
    self.goTo(self,index)
    
  def goTo(self,row = 0):
    """
    Sets the current row to a given index
    """
    if row < self._meta["length"]:
      self._meta["index"] = row
    
  def search(self,**kwargs):
    """
    Searches for a given combination of values in the datacube, starting from index "start".
    Example: datacube.search(a = 4, b = -3,c = 2,start = 0) will return the index of the first row where a == 4, b == -3, c == 2,
    starting at index 0. If no row matches the given criteria, search will return [].
    """
    keys = kwargs.keys()
    cols = dict()
    foundRows = []
    dtype = self.table().dtype
    for key in keys:
      cols[key] = self.column(key)
      if cols[key] == None:
        return []
    for i in range(0,len(cols[keys[0]])):
      found = True
      for key in keys:
        if not allclose(array(kwargs[key],dtype=dtype), cols[key][i]):
          found = False
          break
      if found:
        foundRows.append(i)
    return foundRows
        
  def rowAt(self,index):
    """
    Returns a row at a given index
    """
    if index != None and index < len(self):
      return self._table[index,:]
        
  def row(self):
    """
    Returns the current row
    """
    return self.rowAt(self._meta["index"])
          
  def clearRow(self):
    """
    Sets all values in the current row to 0
    """
    if self._meta["index"] != None:
      for i in range(0,len(self._table[self._meta["index"],:])):
        self._table[self._meta["index"],i] = 0
    self.notify("clearRow")
  
  def setColumn(self,*args,**kwargs):
    """
    Alias for createColumn...
    """
    return self.createColumn(*args,**kwargs)
  
  def createColumn(self,name,values,offset = 0):
    """
    Creates a new column
    """
    index = self.index()
    self.goTo(offset)
    for value in values:
      self.set(**{name:value})
      self.commit()
    self.goTo(index)

  def setAt(self,index,**keys):
    """
    Sets a set of variables at a given index
    """
    oldIndex = self._meta["index"]
    self._meta["index"] = index
    self.set(**keys)
    self.commit()
    self._meta["index"] = oldIndex

  def sortBy(self,column,reverse = False):
    """
    Sorts the datacube by a given variable
    """
    col = list(self.column(column))
    indices = zip(col,range(0,len(col)))
    sortedValues,sortedIndices = zip(*sorted(indices,reverse = reverse))
    self._table = self._table[sortedIndices,:]
    #To do: Add sorting of children!?
    self.notify("sortBy",column)

  def set(self,**keys):
    """
    Sets a pair of variables in the current row
    """
    currentShape = shape(self._table)
    if self._meta["index"] >= currentShape[0]:
      self._resize((self._meta["index"]+10001,len(self._meta["fieldNames"])))
    for key in keys:
      i = self._meta["fieldMap"].get(key)
      if i == None:
        self._meta["fieldNames"].append(key)
        self._adjustTable()
        i = self._meta["fieldMap"].get(key)
      self._table[self._meta["index"],i] = keys[key]
    
  def removeRow(self,row):
    """
    Removes a given row from the datacube.
    """
    if row < len(self)-1:
      self._table[row:-1,:] = self._table[row+1:,:]
    self._meta["length"] -= 1
    if self._meta["index"] >= row:
      self._meta["index"]-=1
    self.notify("removeRow",row)
      
  
  def removeRows(self,rows):
    """
    Removes a list of rows from the datacube.
    """
    sortedRows = sorted(rows)
    for row in sortedRows:
      self.removeRow(row)
    
    
  def removeChildren(self,cubes):
    for cube in cubes:
      self.removeChild(cube)
  
  def removeChild(self,child,eraseChild = False):
    """
    Removes a given child cube from the datacube
    """
    for item in self._children:
      if item.datacube() == child:
        item.datacube().setParent(None)
        del self._children[self._children.index(item)]
        self.notify("removeChild",item.datacube())
        return
  
  def addChild(self,cube,**kwargs):
    """
    Adds a child to the datacube
    """
    if cube in self.children():
      raise Exception("Datacube is already a child!")
    attributes = kwargs
    if not "row" in attributes:
      attributes["row"] = self.index()
    item = ChildItem(cube,attributes)
    if cube.parent() != None:
      cube.parent().removeChild(cube)
    cube.setParent(self)
    self._children.append(item)
    self.notify("addChild",cube)
    self.setModified()
      
  def setModified(self):
    """
    Marks the datacube as modified
    """
    self._meta["modificationTime"] = time.asctime()
    self._unsaved = True

  def attributesOfChild(self,child):
    if child in map(lambda x:x.datacube(),self._children):
      i = map(lambda x:x.datacube(),self._children).index(child)
      return self._children[i].attributes()
    raise AttributeError("Child not found!")
    
  def setChildAttributes(self,child,**kwargs):
    attributes = self.attributesOfChild(child)
    for key in kwargs:
      attributes[key] = kwargs[key]

  def children(self,**kwargs):
    """
    Returns the children dictionary of the daacube
    """
    if kwargs == {}:
      return map(lambda x:x.datacube(),self._children)
    else:
      children = []
      for item in self._children:
        deviate = False
        for key in kwargs:
          if (not key in item.attributes()) or item.attributes()[key] != kwargs[key]:
            deviate = True
            continue
        if not deviate:
          children.append(item.datacube())
      return children             
    
  def __getitem__(self,keys):
    if not hasattr(keys,'__iter__'):
      keys = [keys]
    return self.columns(keys)
        
  def setChanged(self,changed = False):
    """
    Marks the datacube as changed
    """
    self._changed = changed
    
  def changed(self):
    """
    Returns True if the datacube has been changed but not saved
    """
    return self._changed
            
  def names(self,includeChildren = False):
    """
    Returns all column names of the datacube (and optionally also of all children)
    """
    names = self._meta["fieldNames"]
    if includeChildren == False:
      return names
    for cube in map(lambda x:x.datacube(),self._children):
      subnames = cube.names()
      for subname in subnames:
        if not subname in names:
         names.append(subname)
    return names
  
  def _resize(self,size):
    """
    Resizes the datacube
    """
    self._table.resize(size,refcheck = False)

  def commit(self):
    """
    Commits a new line to the datacube
    """
    if self._meta["index"] >= self._meta["length"]:
      self._meta["length"] = self._meta["index"]+1
    self.setModified()
    self.notify("commit",self._meta["index"])
    self._meta["index"]+=1
    
  def __len__(self):
    """
    Returns the length (i.e. the number of rows) of the datacube
    """
    return self._meta["length"]  
  
  def loadTable(self,filename,delimiter = "\t",guessStructure = False):
    """
    Loads the table of the datacube from a text file
    """
    file = open(filename,"r")
    contents = file.read()
    file.close()
    lines = contents.split("\n")
    if guessStructure:
      self._meta["fieldNames"] = lines[0].split(delimiter)
      self._meta["length"] = len(lines)-1
      if lines[1].find("j") == -1:
        self._meta["dataType"] = float64
      else:
        self._meta["dataType"] = complex128
    self._table = zeros((len(lines[1:]),len(self._meta["fieldNames"])),dtype = self._meta["dataType"])
    self._meta["length"] = 0
    i = 0
    for line in lines[1:]:
      entries = line.split(delimiter)
      j = 0
      if line == "":
        continue
      for entry in entries:
        if entry != "":
          if self._meta["dataType"] == complex128:
            value = complex(entry)
          elif self._meta["dataType"] == bool:
            if entry == "False":
              value = 0
            else:
              value = 1
          else:
            value = float(entry)
          if j < len(self._meta["fieldNames"]) and i < self._table.shape[0]:
            self._table[i,j] = value
          j+=1
      self._meta["length"]+=1
      i+=1
          
  def loadFromHdf5(self,path,verbose = False):

    import h5py
    
    """
    Loads the datacube from a HDF5 file.
    """
    
    dataFile = h5py.File(path,"r")
    
    self.loadFromHdf5Object(dataFile,verbose = verbose)

    dataFile.close()
    
  
  def saveToHdf5(self,path = None,saveChildren = True,overwrite = False,forceSave = False,verbose = False):

    import h5py

    """
    Saves the datacube to a HDF5 file 
    """

    if path == None and self.filename() != None:
      path = self.filename()
      overwrite = True

    elif path == None and self.name() != None:
      path = self.name()+".hdf"
      
    if path == None:
      raise Exception("You must supply a filename!")
    
    if verbose:
      print "Creating HDF5 file at %s" % path
    
    dataFile = h5py.File(path,"w")

    self.saveToHdf5Object(dataFile,saveChildren,overwrite,forceSave,verbose = verbose)
    self._meta["modificationTime"] = os.path.getmtime(path)
    self.setFilename(path)

    dataFile.flush()
    dataFile.close()
  
    
  def loadFromHdf5Object(self,dataFile,verbose = False):

    """
    Loads the datacube from a HDF5 group
    """
    
    version = dataFile.attrs["version"]
    
    if version in ["0.1","0.2"]:
      self._meta = yaml.load(dataFile.attrs["meta"])
      self._parameters = yaml.load(dataFile.attrs["parameters"])
    
    if len(self)>0:   
      ds = dataFile["table"]
      self._table = empty(shape=ds.shape, dtype=ds.dtype)
      self._table[:] = ds[:]
    
    self._adjustTable()
    self._children = []
    
    for key in sorted(map(lambda x:int(x),dataFile['children'].keys())):
      child = dataFile['children'][str(key)]
      cube = Datacube()
      cube.loadFromHdf5Object(child)
      attributes = yaml.load(child.attrs["attributes"])
      self.addChild(cube,**attributes)
      
    return True

  def saveToHdf5Object(self,dataFile,saveChildren = True,overwrite = False,forceSave = False,verbose = False):

    """
    Saves the datacube to a HDF5 group
    """

    dataFile.attrs["version"] = Datacube.version
    dataFile.attrs["meta"] = yaml.dump(self._meta)
    dataFile.attrs["parameters"] = yaml.dump(self._parameters)
    
    if len(self)>0:
      dataFile.create_dataset('table',data = self.table())   

    childrenFile = dataFile.create_group("children")

    #We save the child cubes
    if saveChildren:
      cnt = 0
      for item in self._children:
        childFile = childrenFile.create_group(str(cnt))
        childFile.attrs["attributes"] = yaml.dump(item.attributes())
        child = item.datacube()
        child.saveToHdf5Object(childFile,verbose = verbose)
        cnt+=1
        
    self._unsaved = False
    return True

  def saveTable(self,filename,delimiter = "\t",header = None):
    """
    Saves the data table to a given file
    """
    file = open(filename,"w")
    headers = ""
    for name in self.names():
      headers+=name+"\t"
    headers = string.rstrip(headers)+"\n"
    if header != None:
      file.write(header)
    file.write(headers)
    s = self._table.shape
    for i in range(0,min(s[0],self._meta["length"])):
      line = ""
      for j in range(0,len(self._meta["fieldNames"])):
        numberstr = str(self._table[i,j])
        if numberstr[0] == '(':
          numberstr = numberstr[1:-1]
        line+=numberstr
        if j != len(self._meta["fieldNames"])-1:
          line+=delimiter
      line+="\n"
      file.write(line)
    file.close()
  
  def savetxt(self,path = None,saveChildren = True,overwrite = False,forceSave = False,allInOneFile = False):

    """
    Saves the datacube to a text file
    """

    if path == None and self.filename() != None:
      path = self.filename()
      overwrite = True
    elif path == None and self.name() != None:
      path = self.name()
    if path == None:
      raise Exception("You must supply a filename!")
    
    path = re.sub(r"\.[\w]{3}$","",path)
    directory = os.path.abspath(os.path.dirname(path))
    filename = os.path.split(path)[1]
    filename = self._sanitizeFilename(filename)
    #We determine the basename of the file to which we want to save the datacube.
    basename = filename

    cnt = 1

    if overwrite == False:
      while os.path.exists(directory+"/"+basename+".txt"):
        basename = filename+"-"+str(cnt)
        cnt+=1

    savename = basename+".txt"
    savepath = directory+"/"+savename
    parpath = directory+"/"+basename+".par"

    children = []

    #We save the child cubes
    if saveChildren:
      for i in range(0,len(self._children)):
        item = self._children[i]
        child = item.datacube()
        if child.name() != None:
          childfilename = basename+"-"+child.name()+("-%d" % (i))
        else:
          childfilename = basename+("-%d" % (i))
        childPath = child.savetxt(directory+"/"+childfilename,saveChildren = saveChildren,overwrite = True,forceSave = forceSave)
        children.append({'attributes':item.attributes(),'path':childPath})

    if os.path.exists(savepath) and os.path.getmtime(savepath) <= self._meta["modificationTime"] and os.path.exists(parpath) and os.path.getmtime(parpath) <= self._meta["modificationTime"]:
      if self._unsaved == False and forceSave == False:
        return basename

    #We save the datacube itself

    self.setFilename(parpath)
    
    paramsDict = dict()
    paramsDict['version'] = Datacube.version
    paramsDict['meta'] = copy.copy(self._meta)
    paramsDict['parameters'] = self.parameters()
    paramsDict['children'] = children
    paramsDict['tablefilename'] = savename

    paramstxt = yaml.dump(paramsDict)

    if not allInOneFile:
      params = open(parpath,"w")
      params.write(paramstxt)
      params.close()
      self.saveTable(savepath)
    else:
      lines = paramstxt.split("\n")
      paramstxt = "#"+"\n#".join(lines)
      self.saveTable(savepath,header = paramstxt)

    self._unsaved = False
    self._meta["modificationTime"] = os.path.getmtime(savepath)

    return basename
        
  def name(self):
    """
    Returns the name of the datacube
    """
    return self._meta["name"]
        
  def setName(self,name):
    """
    Sets the name of the datacube
    """
    self._meta["name"] = str(name)    
    self.setModified()
    self.notify("name",name)
  
  def childrenAt(self,row):
    """
    Returns all child cubes at row [row]
    """
    return self.children(row = row)
      
  def _sanitizeFilename(self,filename):
    """
    Used to clean up the filename and remove all unwanted characters
    """
    filename = re.sub(r'\.','p',filename)    
    filename = re.sub(r'[^\=\_\-\+\w\d\[\]\(\)\s\\\/]','-',filename)
    return filename
    
  def save(self,filename,format = 'pickle'):
    """
    Dumps the datacube to a pickled string
    """
    self._resize((self._meta["length"],len(self._meta["fieldNames"])))
    f = open(filename,"wb")
    return pickle.dump(self,f)

  def load(self,filename):
    """
    Loads the datacube from a pickled file
    """
    f = open(filename,"rb")
    loaded = pickle.load(f)
    self.__dict__ = loaded.__dict__

  def loadstr(self,string):
    """
    Load the datacube from a pickled string
    """
    loaded = pickle.loads(string)
    self.__dict__ = loaded.__dict__

  def loadtxt(self,path,format = 'yaml',loadChildren = True):
    """
    Loads the datacube from a text file
    """
  
    path = re.sub(r"\.[\w]{3}$","",path)
    params = open(path+".par","r")
    filename = os.path.split(path)[1]
    directory = os.path.abspath(os.path.dirname(path))
    data = yaml.load(params.read())          
    params.close()
    
    if "version" in data:
      version = data["version"]
    else:
      version = "undefined"
    
    guessStructure = False
    
    if version in ["0.1","0.2"]:
      self._meta = data["meta"]
      self._parameters = data["parameters"]
    elif version == "undefined":
      print "Undefined version, trying my best to load the datacube..."
      mapping = {"len":"length","index":"index","names":"fieldNames","name":"name","description":"description","tags":"tags","dtype":"dataType"}
      for key in mapping.keys():
        if key in data:
          self._meta[mapping[key]] = data[key]
      
    if "parameters" in data:
      self._parameters = data["parameters"]
    
    self._children = []
    
    if loadChildren:
      if version == "undefined" or version == "0.1":
        for key in data["children"]:
          try:
            for path in data["children"][key]:
              if not os.path.isabs(path):
                path = directory + "/" + path
              datacube = Datacube()
              datacube.loadtxt(path)
              attributes = {"row" : key}
              item = ChildItem(datacube,attributes)
            self._children.append(item)
          except:
            self.removeChild(datacube)
            print "cannot load 1 datacube"
      elif version == "0.2":
        for child in data['children']:
          try:
            datacube = Datacube()
            path = child["path"]
            if not os.path.isabs(path):
              path = directory + "/" + path
            datacube.loadtxt(path)
            self.addChild(datacube,**child["attributes"])
          except:
            self.removeChild(datacube)
            print "cannot load 1 datacube"

    tableFilename = directory+"/"+data['tablefilename']

    self.loadTable(tableFilename,guessStructure = guessStructure)
    self._meta["modificationTime"] = os.path.getmtime(directory+"/"+data['tablefilename'])

    self._adjustTable()
    self.setFilename(directory+"/"+filename+".par")
