import urllib2,urllib,cookielib

import creole,creole2html
import latex

teststring = '''
=Heading 1

==Heading 2

* A list 
** An item
** Another item

[[Link to|some site]]

{{image|this is the caption}}

** bold and //italic// **

$$This should be formatted as math$$

|=Heading this is a|=Heading table|
|=right first row|second row|
'''

latex_test = '''
\section{Heading {Tricky} {Even more tricky {Tricky escaped \} \} \{ bogus block \{ tricky} } 1}
The first section

\\textbf{This is fat!!!}

\\{this is not a block}
\subsection{Heading 2}
The second section

\\begin{itemize}
\\item{A list}
  \\begin{enumerate}
    \\item{An item }
    \\item [optional args]{  \\textbf{Another item}}
  \\end{enumerate}
\\end{itemize}

$$This should be formatted as math $$


This text comprises one paragraph and should be formatted as such.

This is also part of the paragraph.


\\begin{tabular}{|lrrr|}[center][some more arguments]
this is & a table \\\\
first row & second row \\\\
\\end{tabular}

\\textb{}
'''


#my_parser = creole.Parser(teststring)

#print creole2html.HtmlEmitter(my_parser.parse()).emit()

file = open('thesis.tex')

content = file.read()

latex_parser = latex.Parser(content)

result = latex_parser.parse()

#print latex_parser.renderCode()

if latex_parser.renderCode() != content:
  print "Try again!"
else:
  print "Success!"

reconstructed = open('reconstructed.txt','w')
reconstructed.write(latex_parser.renderCode())

print "Document structure:"

fileoutput = open('file_output.html','w')
fileoutput.write(latex_parser.render())

struct = open('struct.txt','w')
struct.write(latex_parser.documentStructure())

exit(0)

from multipart import *

cookies = cookielib.CookieJar()

server= 'http://192.168.0.11:3000'


data =   {
  'email' : 'andreasdewes@gmx.de',
  'password' : 'test',
}

file =open('exp-strombergxvid-s04e02.avi','rb')


content = file.read(1024*1024*10)


headers = {
  'Accept' : 'text/xml'
}

cookie_handler = urllib2.HTTPCookieProcessor(cookies)


redirect_handler= urllib2.HTTPRedirectHandler()
o = urllib2.build_opener( cookie_handler,redirect_handler,urllib2.HTTPHandler())

urllib2.install_opener(o)

authenticity = urllib2.Request(server+'/login/get_token',headers = headers)
response = o.open(authenticity)


token = response.read()
print cookies

data['authenticity_token'] = token

files = [('test','testfile.pdf',content)]
encoded = encode_multipart_formdata(data,files)

senddata = encoded[1]

headers['content-type'] = encoded[0]

authenticity = urllib2.Request(server+'/login/index',headers = headers,data =senddata)
response = o.open(authenticity)

print response.read()

print cookies

del headers['content-type']

projects = urllib2.Request(server+'/projects/index',headers = headers)

response = o.open(projects)

print response.read()
