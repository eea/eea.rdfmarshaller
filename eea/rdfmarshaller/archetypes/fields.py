""" Archetypes Field2Surf field adapters
"""
import sys

import rdflib
import surf
from eea.rdfmarshaller.archetypes.interfaces import (IATField2Surf,
                                                     IReferenceField)
from eea.rdfmarshaller.generic.fields import BaseShortenHTMLField2Surf
from eea.rdfmarshaller.interfaces import ISurfSession
from Products.Archetypes.interfaces import IField, IFileField
from Products.CMFPlone import log
from zope.component import adapts
from zope.interface import Interface, implements


class ATField2Surf(object):
    """Base implementation of IATField2Surf """

    implements(IATField2Surf)
    adapts(IField, Interface, ISurfSession)

    exportable = True
    prefix = None   # override the prefix for this predicate
    name = None     # this will be the predicate name (fieldname)

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

    @property
    def name(self):
        """ return field name """

        return self.field.getName()

    def value(self):
        """ The desired output is similar to:
        <report:file>
          <schema:MediaObject rdf:about="
                http://random-url/publications/emep-eea-guidebook-2016/file">
            <eea:fileInfo rdf:resource="
                http://random-url/publications/emep-eea-guidebook-2016/
                file#fileInfo"/>
          </schema:MediaObject>
        </report:file>

        For files:
        <dcat:Distribution rdf:about="
            http://random-url/publications/emep-eea-guidebook-2016/
            file#fileInfo">
          <dcat:downloadURL rdf:resource="
            http://random-url/publications/emep-eea-guidebook-2016/
            at_download/file"/>
          <dcat:sizeInBytes rdf:datatype="
            http://www.w3.org/2001/XMLSchema#integer">844</dcat:sizeInBytes>
        </dcat:Distribution>

        For images:
        <dcat:Distribution rdf:about="
            http://random-url/articles/alpler/image#fileInfo">
          <dcat:downloadURL rdf:resource="
            http://random-url/articles/alpler/at_download/image"/>
          <dcat:sizeInBytes rdf:datatype="
            http://www.w3.org/2001/XMLSchema#integer">844</dcat:sizeInBytes>
        </dcat:Distribution>
        """

        name = self.field.getName()
        base_url = self.context.absolute_url()
        field_url = "{0}/{1}".format(base_url, name)
        download_url = '{0}/at_download/{1}'.format(base_url, name)

        # 22047 check if value isn't a false value, images with no data
        # will return an empty string
        # value = self.field.getAccessor(self.context)()
        size = self.field.get_size(self.context)

        if not size:
            return

        Distribution = self.session.get_class(surf.ns.DCAT['Distribution'])
        dist = Distribution(field_url + "#fileInfo")
        dist.dcat_sizeInBytes = size
        dist.dcat_downloadURL = rdflib.URIRef(download_url)
        dist.update()

        MediaObject = self.session.get_class(surf.ns.SCHEMA['MediaObject'])
        ff = MediaObject(field_url)
        ff.eea_fileInfo = dist
        ff.update()
        ff.save()

        return rdflib.URIRef(field_url)


class ATReferenceField2Surf(ATField2Surf):
    """IATField2Surf implementation for Reference fields"""

    implements(IATField2Surf)
    adapts(IReferenceField, Interface, ISurfSession)

    def value(self):
        """ Value """
        value = self.field.getAccessor(self.context)()

        # some reference fields are single value only

        if not isinstance(value, (list, tuple)):
            value = [value]

        value = [v for v in value if v]     # the field might have been empty

        return [rdflib.URIRef(obj.absolute_url()) for obj in value]


class ShortenHTMLField2Surf(ATField2Surf, BaseShortenHTMLField2Surf):
    """ A superclass to be used to provide alternate values for fields

    To use it, inherit from this class and override the alternate_field prop:

    class FallbackDescription(ShortenHTMLField2Surf):
        alternate_field = "text"

    <adapter
        for="* eea.indicators.specification.Specification *"
        name="description"
        factory=".FallbackDescription"
        />
    """

    alternate_field = None

    def get_raw_value(self):

        if not self.alternate_field:
            raise ValueError
        field = self.context.getField(self.alternate_field)
        accessor = field.getAccessor(self.context)

        return accessor()

    def value(self):
        v = ATField2Surf(self.field, self.context, self.session).value()

        return v or self.alternate_value()
