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

#This is a hirarchical data storage class. A datacube stores a 2-dimensional array of values. Each array column is identified by a name. In addition, you can add one or more "child datacubes" to each row of the array, thus creating a multidimensional data model.
class Datacube(Subject,Observer,Reloadable):
  
  def __getstate__(self):
    variables = Subject.__getstate__(self)
    del variables["_parent"]
    return variables
    
  def __setstate__(self,state):
    Subject.__setstate__(self,state)
    self.__dict__ = state
    for child in self.allChildren():
      child.setParent(self)

  def __init__(self,name = "datacube",description = None,filename = None,dtype = float64):
    Subject.__init__(self)
    Observer.__init__(self)
    Reloadable.__init__(self)
    self._filename = filename
    self._name = name
    self._description = description
    self._names = []
    self._map = dict()
    self._dim = None
    self._column = None
    self._children = dict()
    self._parent  = None
    self._parameters = dict()
    self._index = 0
    self._dtype = dtype
    self._len = 0
    self._name = name
    self._table = None
    self._description = ""
    self._tags = ""
    self._tablemtime = 0
    self._parmtime = 0
    self._roles = dict()
    self._changed = False
    self._created = time.asctime()
    self._modified = time.asctime()
    self._unsaved = True
    self.adjustTable()
    
  def setRoles(self,variable,roles):
    """
    Sets the roles of a given variable
    """
    self._roles[variable] = roles

  def addRoles(self,variable,roles):
    """
    Adds a role to a given variable
    """
    if variable not in self._roles:
      self._roles[variable] = []
    for role in roles:
      if role not in self._roles[variable]:
        self._roles[variable].append(role)
  
  def variablesWithRoles(self,roles):
    """
    Returns a list of variables such that all of them have all roles as given in "roles".
    """
    variables = []
    for variable in self._names:
      if variable in self._roles:
        found = False
        for role in roles:
          if role not in self._roles[variable]:
            found = True
            break
        if found == False:
          variables.append(variable)
    return variables
    
  def roles(self,variable):
    """
    Returns the roles of a given variable
    """
    if variable in self._roles:
      return self._roles[variable]
    return None
    
  def parameters(self):
    """
    Returns the parameters of the datacube
    """
    return self._parameters
    
  def setParameters(self,params):
    """
    Sets the parameters of the datacube
    """
    self._parameters = params
    self.setModified()
    self.notify("parameters",params)
    
    
  def setFilename(self,filename):
    """
    Sets the filename of the datacube
    """
    self._filename = os.path.realpath(filename)
    self.setModified()
    self.notify("filename",filename)
    
  def filename(self):
    """
    Returns the filename of the datacube
    """
    return self._filename
    
  def parent(self):
    """
    Returns the parent of the datacube
    """
    if self._parent == None:
      return None
    return self._parent()
  
  def tags(self):
    """
    Returns the tags of the datacube
    """
    return self._tags
    
  def description(self):
    """
    Returns the description of the datacube
    """
    return self._description
    
  def setTags(self,tags):
    """
    Sets the tags of the datacube
    """
    self._tags = str(tags)
    self.setModified()
    self.notify("tags",tags)
    
  def setDescription(self,description):
    """
    Sets the description of the datacube
    """
    self._description = str(description)
    self.setModified()
    self.notify("description",description)
  
  def structure(self,tabs = ""):
    """
    Returns a string describing the structure of the datacube
    """
    string = tabs+"cube(%d,%d)" % (self._len,self._dim)+"\n"
    for key in self._children:
      string+=tabs+"%d children at row %d:" % (len(self._children[key]),key)+"\n"
      for child in self._children[key]:
        string+=child.structure(tabs+"\t")
    return string
   
  def columns(self,names):
    """
    Returns a table containing a set of given columns
    """
    table = zeros((self._len,len(names)),dtype = self._dtype)
    for i in range(0,len(names)):
      table[:,i] = self.column(names[i])
    return table
    
  def columnName(self,index):
    for key in self._map.keys():
      if self._map[key] == index:
        return key
    return None
    
  def column(self,name):
    """
    Returns a given column of the datacube
    """
    if name in self._map:
      return self._table[:self._len,self._map[name]]

  def addRow(self):
    s = shape(self._table)
    if s[0] < self._len+1:
      self._table.resize((s[0]+1,s[1]))
    self._len+=1
  
  def adjustTable(self):
    """
    Resizes the table, if necessary
    """
    if self._table == None: 
      self._table=zeros((self._len+1,len(self._names)),dtype = self._dtype)
    elif shape(self._table)[1] < len(self._names):
      newarray = zeros((len(self._table),len(self._names)),dtype = self._dtype)
      newarray[:,:len(self._table[0,:])]=self._table
      self._table = newarray
      self.notify("names",self._names)
    self._dim = len(self._names)
    for i in range(0,len(self._names)):
      self._map[self._names[i]] = i
      
  def len(self):
    """
    Returns the length of the datacube
    """
    return self._len
          
  def clear(self):
    """
    Resets the datacube to its initial state
    """
    self._table = None
    self._index = 0
    self._len = 0
    self._dim = 0
    self._names = []
    self._map = dict()
    
    self.removeChildren(self.allChildren())
    
    self._roles = dict()
    self.adjustTable()
    self.notify("clear")

  def table(self):
    """
    Returns the data table
    """
    return self._table[:self._len,:]
    
  def goTo(self,row = 0):
    """
    Sets the current row to a given index
    """
    if row < self._len:
      self._index = row

  def searchChildren(self,**kwargs):
    indices = self.search(**kwargs)
    children = []
    for index in indices:
      children.extend(self.childrenAt(index))
    return children
    
  def search(self,**kwargs):
    """
    Searches for a given combination of values in the datacube, starting from index "start".
    Example: datacube.search(a = 4, b = -3,c = 2,start = 0) will return the index of the first row where a == 4, b == -3, c == 2,
    starting at index 0. If no row matches the given criteria, search will return None.
    """
    keys = kwargs.keys()
    cols = dict()
    foundRows = []
    for key in keys:
      cols[key] = self.column(key)
      if cols[key] == None:
        return None
    for i in range(0,len(cols[keys[0]])):
      found = True
      for key in keys:
        if cols[key][i] != kwargs[key]:
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
    return self.rowAt(self._index)
          
  def clearRow(self):
    """
    Sets all values in the current row to 0
    """
    if self._index != None:
      for i in range(0,len(self._table[self._index,:])):
        self._table[self._index,i] = 0
    self.notify("clearRow")
  
  def createColumn(self,name,values,offset = 0):
    """
    Creates a new column
    """
    self.goTo(offset)
    index = self._index
    for value in values:
      self.set(**{name:value})
      self.commit()

  def setAt(self,index,**keywords):
    """
    Sets a set of variables at a given index
    """
    if index >= len(self):  
      return False
    oldIndex = self._index
    self._index = index
    self.set(**keywords)
    self._index = oldIndex
    self.notify("commit",index)

  def sortBy(self,column,reverse = False):
    """
    Sorts the datacube by a given variable
    """
    col = list(self.column(column))
    indices = zip(col,range(0,len(col)))
    sortedValues,sortedIndices = zip(*sorted(indices,reverse = reverse))
    self._table = self._table[sortedIndices,:]
    newChildren = dict()
    print len(indices)
    for i in range(0,len(sortedIndices)):
      if sortedIndices[i] in self._children:
        children = []
        children.extend(self._children[sortedIndices[i]])
        self.removeChildren(children)
        newChildren[i] = children
    for key in newChildren:
      for child in newChildren[key]:
        self.addChildAt(key,child)
    self.notify("sortBy",column)

  def addVariables(self,variables):
    for var in variables:  
      self._names.append(var)
    self.adjustTable()

  def set(self,**keywords):
    """
    Sets a pair of variables in the current row
    """
    currentShape = shape(self._table)
    if self._index >= currentShape[0]:
      self._resize((self._index+10001,self._dim))
    for keyword in keywords:
      i = self._map.get(keyword)
      if i == None:
        self._names.append(keyword)
        self.adjustTable()
        i = self._map.get(keyword)
      self._table[self._index,i] = keywords[keyword]
  
  def removeRows(self,rows):
    """
    Removes a list of rows from the datacube.
    """
    sortedRows = sorted(rows)
    while len(sortedRows) > 0:
      row = sortedRows.pop()
      if row in self._children:
        self.removeChildren(self._children[row])
      for childRow in self._children.keys():
        if childRow > row:
          self._children[childRow-1] = self._children[childRow]
          del self._children[childRow]
      if row < len(self):
        self._table[row:-1,:] = self._table[row+1:,:]
      self._len -= 1
      self._index-=1
      
    
  def removeChildren(self,cubes):
    for cube in cubes:
      self.removeChild(cube)
  
  def removeChild(self,cube):
    """
    Removes a given child cube from the datacube
    """
    for index in self._children.keys():
      for child in self._children[index]:
        if child == cube:
          self.notify("removeChild",child)
          i = self._children[index].index(child)
          del self._children[index][i]
          child.setParent(None)
  
  def addChildAt(self,row,cube):
    """
    Adds a child to the datacube
    """
    if row in self._children:
      self._children[row].append(cube)
    else:
      self._children[row] = [cube]
    self.notify("addChild",cube)
    self.setModified()
    cube.setParent(self)
  
  #Appends a child datacube to the current datapoints. This allows for the efficient storage of hirarchical data.
  def addChild(self,cube):
    self.addChildAt(self._index,cube)
    
  def setModified(self):
    """
    Marks the datacube as modified
    """
    self._modified = time.asctime()
    self._unsaved = True
    
  def setParent(self,parent):
    """
    Sets the parent of the datacube
    """
    if parent != None:
      self._parent = weakref.ref(parent)
    else:
      self._parent = None

  def children(self):
    """
    Returns the children dictionary of the daacube
    """
    return self._children
    
  def allChildren(self):
    """
    Returns all the children of the datacube
    """
    children = []
    for child in self._children.keys():
      children.extend(self._children[child])
    return children
    
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
    names = self._names
    if includeChildren == False:
      return names
    for cubes in self._children.values():
      for cube in cubes:
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
    self.notify("commit",self._index)
    self.setModified()
    self._index+=1
    if self._index > self._len:
      self._len = self._index
    
  def __len__(self):
    """
    Returns the length (i.e. the number of rows) of the datacube
    """
    return self._len  
  
  def loadTable(self,filename,delimiter = "\t"):
    """
    Loads the table of the datacube from a text file
    """
    self._table = zeros((self._len,self._dim),dtype = self._dtype)
    file = open(filename,"r")
    contents = file.read()
    file.close()
    lines = contents.split("\n")
    i = 0
    for line in lines[1:]:
      entries = line.split(delimiter)
      j = 0
      for entry in entries:
        if entry != "":
          if self._dtype == complex128:
            number = complex(entry)
          else:
            number = float(entry)
          if j < self._dim:
            self._table[i,j] = number
          j+=1
      i+=1
      
  def savetxt(self,filename,delimiter = "\t"):
    """
    Saves the table of the datacube to a text file
    """
    file = open(filename,"w")
    headers = ""
    for name in self.names():
      headers+=name+"\t"
    headers = string.rstrip(headers)+"\n"
    file.write(headers)
    for i in range(0,self._len):
      line = ""
      for j in range(0,self._dim):
        numberstr = str(self._table[i,j])
        if numberstr[0] == '(':
          numberstr = numberstr[1:-1]
        line+=numberstr
        if j != self._dim-1:
          line+=delimiter
      line+="\n"
      file.write(line)
    file.close()
    
  def loadFromHdf5(self,path):

    import h5py
    
    """
    Loads the datacube from a HDF5 file.
    """
    
    dataFile = h5py.File(path,"r")
    
    self.loadFromHdf5Object(dataFile)

    dataFile.close()
    
  
  def saveToHdf5(self,path = None,saveChildren = True,overwrite = False,forceSave = False):

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
    
    dataFile = h5py.File(path,"w")

    self.saveToHdf5Object(dataFile,saveChildren,overwrite,forceSave)

    self._tablemtime = os.path.getmtime(path)
    self._parmtime = self._tablemtime

    dataFile.flush()
    dataFile.close()
  
  def equal(self,a):  
    """
    Checks if two datacubes are equal
    """
    if self.name() != a.name():
      return False
    if self.description() != a.description():
      return False
    if self.names() != a.names():
      return False
    if self.parameters() != a.parameters():
      return False
    if not allclose(self.table(),a.table()):
      return False
    allChildren = self.allChildren()
    allChildrenA = a.allChildren()
    if len(allChildren) != len(allChildrenA):
      return False
    for i in range(0,len(allChildren)):
      if allChildren[i].equal(allChildrenA[i]) == False:
        return False
    return True
  
  def not_equal(self,a):
    return not self.__eq__(a)
    
  def loadFromHdf5Object(self,dataFile):

    """
    Loads the datacube from a HDF5 group
    """
    
    params = yaml.load(dataFile.attrs["parameters"])

    for key in params.keys():
      if hasattr(self,"_%s" % key):
        self.__dict__["_%s" % key] = params[key]
    
    if len(self)>0:   
      ds = dataFile["table"]
      self._table = empty(shape=ds.shape, dtype=ds.dtype)
      self._table[:] = ds[:]
    
    self.adjustTable()

    self._children = dict()

    for row in dataFile['children'].keys():
      childRowObject = dataFile['children'][row]
      self._children[int(row)] = [None]*len(childRowObject)
      for key in childRowObject.keys():
        child = childRowObject[key]
        index = int(key)
        cube = Datacube()
        cube.loadFromHdf5Object(child)
        self._children[int(row)][index] = cube
    
    return True

  def saveToHdf5Object(self,dataFile,saveChildren = True,overwrite = False,forceSave = False):

    """
    Saves the datacube to a HDF5 group
    """

    paramsDict = {'roles':self._roles,'dtype' : self._dtype,'created':self._created,'modified':self._modified,'parameters':self._parameters,'description':self._description,'tags':self._tags,'len':self._len,'name':self._name,'names':self._names,'dim':self._dim,'index':self._index}

    paramstxt = yaml.dump(paramsDict)

    dataFile.attrs["parameters"] = paramstxt
    
    if len(self)>0:
      dataFile["table"] = self.table()    

    childrenFile = dataFile.create_group("children")

    #We save the child cubes
    if saveChildren:

      for key in self._children.keys():
        
        childRowFile = childrenFile.create_group(str(key))
        grandchildren = self._children[key]

        for i in range(0,len(grandchildren)):
          child = grandchildren[i]
          childFile = childRowFile.create_group(str(i))
          child.saveToHdf5Object(childFile)

    self._unsaved = False
    
    return True

  def saveTable(self,filename,delimiter = "\t"):
    """
    Saves the data table to a given file
    """
    file = open(filename,"w")
    headers = ""
    for name in self.names():
      headers+=name+"\t"
    headers = string.rstrip(headers)+"\n"
    file.write(headers)
    s = self._table.shape
    for i in range(0,min(s[0],self._len)):
      line = ""
      for j in range(0,self._dim):
        numberstr = str(self._table[i,j])
        if numberstr[0] == '(':
          numberstr = numberstr[1:-1]
        line+=numberstr
        if j != self._dim-1:
          line+=delimiter
      line+="\n"
      file.write(line)
    file.close()
  
  def savetxt(self,path = None,saveChildren = True,overwrite = False,forceSave = False):

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

    children = dict()

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

    #We save the child cubes
    if saveChildren:

      for key in self._children.keys():

        grandchildren = self._children[key]
        children[key] = []
        cnt = 0

        for child in grandchildren:

          if child.name() != None:

            childfilename = basename+"_"+child.name()+("-%d_%d" % (key,cnt))

          else:

            childfilename = basename+("-%d_%d" % (key,cnt))

          children[key].append(child.savetxt(directory+"/"+childfilename,saveChildren = saveChildren,overwrite = True,forceSave = forceSave))
          cnt+=1

    if os.path.exists(savepath) and os.path.getmtime(savepath) <= self._tablemtime and os.path.exists(parpath) and os.path.getmtime(parpath) <= self._parmtime:
      if self._unsaved == False and forceSave == False:
        return basename

    #We save the datacube itself

    self.setFilename(parpath)
    self.saveTable(savepath)

    self._tablemtime = os.path.getmtime(savepath)

    params = open(parpath,"w")

    paramsDict = {'roles':self._roles,'dtype' : self._dtype,'created':self._created,'modified':self._modified,'parameters':self._parameters,'description':self._description,'tags':self._tags,'len':self._len,'name':self._name,'names':self._names,'dim':self._dim,'index':self._index}
    paramsDict['children'] = children
    paramsDict['tablefilename'] = savename

    paramstxt = yaml.dump(paramsDict)

    params.write(paramstxt)
    params.close()

    self._parmtime = os.path.getmtime(parpath)

    self._unsaved = False

    return basename
        
  def name(self):
    """
    Returns the name of the datacube
    """
    return self._name
        
  def setName(self,name):
    """
    Sets the name of the datacube
    """
    self._name = str(name)    
    self.setModified()
    self.notify("name",name)
  
  def childrenAt(self,row):
    """
    Returns all child cubes at row [row]
    """
    if row in self._children:
      return self._children[row]
    return []
      
  def _sanitizeFilename(self,filename):
    """
    Used to clean up the filename and remove all unwanted characters
    """
    filename = re.sub(r'\.','p',filename)    
    filename = re.sub(r'[^\=\_\-\+\w\d\[\]\(\)\s\\\/]','_',filename)
    return filename
    
  def save(self,filename,format = 'pickle'):
    """
    Dumps the datacube to a pickled string
    """
    self._resize((self._len,self._dim))
    
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
    return pickle.loads(string)

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
    
    for key in data.keys():
      if hasattr(self,"_%s" % key):
        self.__dict__["_%s" % key] = data[key]
    
    self._children = dict()
    
    if loadChildren:
      for key in data['children']:
        cubes = []
        for name in data['children'][key]:
          datacube = Datacube()
          if not os.path.isabs(name):
            name = directory + "/" + name
          datacube.loadtxt(name)
          cubes.append(datacube)
        self._children[key] = cubes

    self.loadTable(directory+"/"+data['tablefilename'])
    self._tablemtime = os.path.getmtime(directory+"/"+data['tablefilename'])

    self.adjustTable()
    self.setFilename(directory+"/"+filename+".par")

    self._parmtime = os.path.getmtime(directory+"/"+filename+".par")