import mimetypes

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields.items():
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="{0!s}"'.format(key))
        L.append('')
        L.append(value)
    if files!= None:
      for (key, filename, value) in files:
          L.append('--' + BOUNDARY)
          L.append('Content-Disposition: form-data; name="{0!s}"; filename="{1!s}"'.format(key, filename))
          L.append('Content-Type: {0!s}'.format(get_content_type(filename)))
          L.append('')
          L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary={0!s}'.format(BOUNDARY)
    return content_type, body

