""" Export module """

import os

from eea.rdfmarshaller.interfaces import ILinkedData
from Products.Marshall.registry import getComponent
from unidecode import unidecode

try:
    LIMIT = int(os.environ.get("RDF_UNICODE_LIMIT", 65535))
except Exception:
    LIMIT = 65535   # Refs #83543 - Default: 0xFFFF, 2^16, 16-bit


class RDFExport(object):
    """ RDF Export """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _sanitize(self, utext, limit=LIMIT):
        """ Sanitize unicode text
        """

        for char in utext:
            if ord(char) > limit:
                yield unidecode(char)
            else:
                yield char

    def sanitize(self, text):
        """ Remove
        """

        if not isinstance(text, unicode):
            text = text.decode('utf-8')

        # Fast sanitize ASCII text
        try:
            text.encode()
        except Exception:
            return u"".join(self._sanitize(text))
        else:
            return text

    def __call__(self):
        marshaller = getComponent('surfrdf')
        endLevel = int(self.request.get('endLevel', 1))
        res = marshaller.marshall(self.context, endLevel=endLevel)

        if not res:
            return ""

        _content_type, _length, data = res

        self.request.response.setHeader('Content-Type',
                                        'application/rdf+xml; charset=utf-8')

        return self.sanitize(data)


class RDFSExport(object):
    """ RDF Surf export """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        marshaller = getComponent('surfrdfs')
        _content_type, _length, data = marshaller.marshall(self.context)
        self.request.response.setHeader('Content-Type',
                                        'application/rdf+xml; charset=utf-8')

        return data


class LinkedDataExport(object):
    """ Export an object as linked data
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):

        marshaller = getComponent('surfrdf')
        obj2surf = marshaller._add_content(self.context)

        if obj2surf is None:
            return ""

        ld = ILinkedData(self.context)

        data = ld.serialize(obj2surf)

        self.request.response.setHeader('Content-Type',
                                        'application/json; charset=utf-8')

        return data
