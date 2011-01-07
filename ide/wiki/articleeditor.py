from pyview.ide.codeeditor import *

class ArticleEditor(LineTextWidget):

  def __init__(self,parent = None):
    LineTextWidget.__init__(self,parent)
    self._article = None
    
  def openArticle(self,article):
    self._article = article
    self.setPlainText(article.text)
    
  def setTabWidget(self,widget):
    self._tabWidget = widget
    

class ArticleEditorWindow(CodeEditorWindow):

    def checkForOpenArticle(self,article):
      for i in range(0,self.Tab.count()):
        if self.Tab.widget(i).fileName() == filename:
          self.Tab.setCurrentWidget(self.Tab.widget(i))
          return True
      return False
      
    def openArticle(self,article):
      MyEditor = ArticleEditor()
      if self.checkForOpenArticle(article):
        return True
      if MyEditor.openArticle(article) == True:
        self.newEditor(MyEditor)
        MyEditor.updateTab()
        return True
      else:
        del MyEditor
      return False
      
    def newEditor(self,Editor = None):
        MyEditor = None
        if Editor != None:
          MyEditor = Editor
        else:
          MyEditor = ArticleEditor()
        MyEditor.setTabWidget(self.Tab)
        self.editors.append(MyEditor)
        self.Tab.addTab(MyEditor,"untitled %i" % self.count)
        self.Tab.setTabToolTip(self.Tab.indexOf(MyEditor),"untitled %i" % self.count)
        self.count = self.count + 1
        self.Tab.setCurrentWidget(MyEditor)
        return MyEditor

    def addEditor(self):
        self.newEditor()
        
    def closeEvent(self,e):
      print "Closing editor window"
      MyPrefs = Preferences()
      openArticles = list()
      for i in range(0,self.Tab.count()):
        widget = self.Tab.widget(i)
        if widget.article() != None:
          openFiles.append(widget.article().id)
        widget.closeEvent(e)
      MyPrefs.set('openArticles',openArticles)
      MyPrefs.save()
        
    def closeTab(self,index):
      window = self.Tab.widget(index)
      if window.close():
        window.destroy()
        self.Tab.removeTab(index)
        if self.Tab.count() == 0:
          self.newEditor()

    def __init__(self,parent=None):
        self.editors = []
        self.count = 1
        CodeEditorWindow.__init__(self,parent)

        MyLayout = QGridLayout()
        
        self.Tab = QTabWidget()
        self.Tab.setTabsClosable(True)
        self.connect(self.Tab,SIGNAL("tabCloseRequested(int)"),self.closeTab)

        MyPrefs = Preferences()
        openArticles = MyPrefs.get('openArticles')
        if openArticles != None:
          for id in openFiles:
            editor = self.newEditor()
            article = Article.get(id)
            if article != None:
              editor.openArticle(article)  
        else:
          self.newEditor()
        MyLayout.addWidget(self.Tab,0,0)

        self.setLayout(MyLayout)
