from DateTime.DateTime import DateTime
from Products.Archetypes.interfaces import IField, IFileField
from Products.CMFPlone import log
from chardet import detect
from eea.rdfmarshaller.archetypes.interfaces import IATField2Surf
from eea.rdfmarshaller.archetypes.interfaces import IReferenceField
from eea.rdfmarshaller.archetypes.interfaces import IValue2Surf
from eea.rdfmarshaller.interfaces import ISurfSession
from zope.component import adapts
from zope.interface import implements, Interface
import rdflib
import sys
import re

import surf

#import logging
#logging.basicConfig(level=logging.CRITICAL)

#===============[ Value Adapters ]=================

class Value2Surf(object):
    """Base implementation of IValue2Surf
    """
    implements(IValue2Surf)
    adapts(Interface)

    def __init__(self, value):
        self.value = value

    def __call__(self, *args, **kwds):
        language = kwds['language']
        if isinstance(self.value, unicode):
            return (self.value, language)
        try:
            value = (unicode(self.value, 'utf-8', 'replace'),
                    language)
        except TypeError:
            value = str(self.value)
        return value


class Tuple2Surf(Value2Surf):
    """IValue2Surf implementation for tuples.
    """
    adapts(tuple)

    def __call__(self, *args, **kwds):
        return list(self.value)


class List2Surf(Value2Surf):
    """IValue2Surf implementation for tuples.
    """
    adapts(list)

    def __call__(self, *args, **kwds):
        return self.value


class String2Surf(Value2Surf):
    """IValue2Surf implementation for strings
    """
    adapts(str)

    _illegal_xml_chars = re.compile(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]')

    def escapeXMLIllegalCharacters(self):
        """Replaces all the XML illegal characters with spaces
        """
        return self._illegal_xml_chars.sub(' ', self.value)


    def __call__(self, *args, **kwds):
        # Stripped illegal xml characters from string
        self.value = self.escapeXMLIllegalCharacters()

        if not self.value.strip():
            return None
        nonEUencodings = ['Big5', 'GB2312', 'EUC-TW', 'HZ-GB-2312',
                          'ISO-2022-CN', 'EUC-JP', 'SHIFT_JIS', 'ISO-2022-JP',
                          'EUC-KR', 'ISO-2022-KR', 'TIS-620', 'ISO-8859-2']
        language = kwds['language']
        encoding = detect(self.value)['encoding']

        if encoding in nonEUencodings:
            value = self.value.decode('utf-8', 'replace')
        else:
            try:
                value = self.value.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                log.log("Could not decode to %s in rdfmarshaller" %
                        encoding)
                value = self.value.decode('utf-8', 'replace')
        return (value.encode('utf-8').strip(), language)


class DateTime2Surf(Value2Surf):
    """IValue2Surf implementation for DateTime """

    adapts(DateTime)

    def __call__(self, *args, **kwds):
        return (self.value.HTML4(), None,
                'http://www.w3.org/2001/XMLSchema#dateTime')


#===============[ Field Adapters ]=================

class ATField2Surf(object):
    """Base implementation of IATField2Surf """

    implements(IATField2Surf)
    adapts(IField, Interface, ISurfSession)

    exportable = True
    prefix = None   #override the prefix for this predicate
    name = None     #this will be the predicate name (fieldname)

    def __init__(self, field, context, session):
        self.field = field
        self.context = context
        self.session = session

    def value(self):
        """ Value """
        try:
            return self.field.getAccessor(self.context)()
        except Exception:
            log.log('RDF marshaller error for context[field]'
                    '"%s[%s]": \n%s: %s' %
                    (self.context.absolute_url(), self.field.getName(),
                     sys.exc_info()[0], sys.exc_info()[1]),
                     severity=log.logging.WARN)

            return None


class ATFileField2Surf(ATField2Surf):
    """IATField2Surf implementation for File fields"""

    implements(IATField2Surf)
    adapts(IFileField, Interface, ISurfSession)

    exportable = True
    prefix = "eea"
    name = "fileInfo"

    def __init__(self, field, context, session):
        self.field = field
        self.context = context
        self.session = session

    def value(self):
        """ The desired output is similar to:
        <datafile:DataFile ...
        ...
            <eea:fileInfo>
                <dcat:Distribution rdf:about="#dist">
                    <dcat:sizeInBytes rdf:datatype="http://www.w3.org/2001/XMLSchema#long">XXXXX</dcat:sizeInBytes>
                    <dcat:downloadURL
                    rdf:resource="[url]/at_download/file"/>
        ...
        </datafile:DataFile>
        """
        #only the size and download ULR are returned
        Distribution = self.session.get_class(surf.ns.DCAT.Distribution)
        fileDistribution = self.session.get_resource('#distribution',
                                                     Distribution)

        value = self.field.getAccessor(self.context)()
        # 22047 check if value isn't a false value, images with no data
        # will return an empty string
        size = value.get_size() if value else 0
        fileDistribution[surf.ns.DCAT['sizeInBytes']] = size

        url = ''.join([self.context.absolute_url(),
                       "/at_download/",
                       self.field.getName()])
        fileDistribution[surf.ns.DCAT['downloadURL']] = rdflib.URIRef(url)
        fileDistribution.update()

        return [fileDistribution]


class ATReferenceField2Surf(ATField2Surf):
    """IATField2Surf implementation for Reference fields"""

    implements(IATField2Surf)
    adapts(IReferenceField, Interface, ISurfSession)

    def value(self):
        """ Value """
        value = self.field.getAccessor(self.context)()

        #some reference fields are single value only
        if not isinstance(value, (list, tuple)):
            value = [value]

        value = [v for v in value if v] #the field might have been empty

        return [rdflib.URIRef(obj.absolute_url()) for obj in value]

