""" Dexterity fields adapters for marshalling """

import sys

import rdflib
import surf
from Acquisition import aq_base
from eea.rdfmarshaller.dexterity.interfaces import IDXField2Surf
from eea.rdfmarshaller.generic.fields import BaseShortenHTMLField2Surf
from eea.rdfmarshaller.interfaces import IFieldDefinition2Surf, ISurfSession
from eea.rdfmarshaller.marshaller import GenericObject2Surf
from eea.rdfmarshaller.value import Value2Surf
from plone.app.textfield.value import RichTextValue
from Products.CMFPlone import log
from zope.component import adapts
from zope.interface import Interface, implements
from zope.schema.interfaces import IField

try:
    from z3c.relationfield.interfaces import IRelationList
    from z3c.relationfield.interfaces import IRelationValue
    HAS_Z3C_RELATIONFIELD = True
except ImportError:
    HAS_Z3C_RELATIONFIELD = False


class DXField2Surf(object):
    """Base implementation of IDXField2Surf """

    implements(IDXField2Surf)
    # adapts(IField, Interface, ISurfSession)
    adapts(Interface, Interface, ISurfSession)

    exportable = True
    prefix = None   # override the prefix for this predicate
    name = None     # this will be the predicate name (fieldname)

    def __init__(self, field, context, session):
        self.field = field
        self.context = context
        self.session = session

        self.name = self.field.__name__

    def value(self):
        """ Value """
        value = getattr(aq_base(self.context), self.name, None)
        try:
            if callable(value):
                value = value()

            return value
        except Exception:
            log.log('RDF marshaller error for context[field]'
                    '"%s[%s]": \n%s: %s' %
                    (self.context.absolute_url(), self.name,
                     sys.exc_info()[0], sys.exc_info()[1]),
                    severity=log.logging.WARN)

            return None


class RichValue2Surf(Value2Surf):
    """ RichTextValue adaptor """
    adapts(RichTextValue)

    def __init__(self, value):
        super(RichValue2Surf, self).__init__(value.output)


class DexterityField2RdfSchema(GenericObject2Surf):
    """IFieldDefinition2Surf implemention for Fields;

    This is used to define rdfs schemas for objects,
    extracting their field definitions
    """

    implements(IFieldDefinition2Surf)
    adapts(IField, Interface, ISurfSession)

    _namespace = surf.ns.RDFS
    _prefix = 'rdfs'

    def __init__(self, context, fti, session):
        super(DexterityField2RdfSchema, self).__init__(context, session)
        self.fti = fti

    @property
    def portalType(self):
        """ portal type """

        return u'Property'

    @property
    def rdfId(self):
        """ rdf id """

        return self.context.getName().replace(' ', '')

    @property
    def subject(self):
        """ subject """

        return '%s#%s' % (self.fti.absolute_url(), self.context.getName())

    def modify_resource(self, resource, *args, **kwargs):
        """ Schema to Surf """
        context = self.context

        # NOTE: To Do: use dexterity mechanism to get widget
        widget_label = (context.title, u'en')
        widget_description = (context.description, u'en')
        fti_title = rdflib.URIRef(u'#%s' % self.fti.Title())

        setattr(resource, 'rdfs_label', widget_label)
        setattr(resource, 'rdfs_comment', widget_description)
        setattr(resource, 'rdf_id', self.rdfId)
        setattr(resource, 'rdf_domain', fti_title.replace(' ', ''))

        return resource


class ShortenHTMLField2Surf(DXField2Surf, BaseShortenHTMLField2Surf):
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

    implements(IDXField2Surf)

    exportable = True
    alternate_field = None

    def get_raw_value(self):
        if not self.alternate_field:
            raise ValueError

        return getattr(self.context, self.alternate_field).output

    def value(self):
        # import pdb; pdb.set_trace()
        v = DXField2Surf(self.field, self.context, self.session).value()

        return v or self.alternate_value()


if HAS_Z3C_RELATIONFIELD:
    class DXRelationList2Surf(DXField2Surf):
        """IATField2Surf implementation for Reference fields"""

        adapts(IRelationList, Interface, ISurfSession)

        def value(self):
            """ Value """
            value = super(DXRelationList2Surf, self).value()

            # some reference fields are single value only

            if not isinstance(value, (list, tuple)):
                value = [value]

            value = [v for v in value if v]   # the field might have been empty

            return [rdflib.URIRef(ref.to_object.absolute_url())
                    for ref in value]

    class RelationValue2Surf(Value2Surf):
        """IValue2Surf implementation for DateTime """

        adapts(IRelationValue)

        def __call__(self, *args, **kwds):

            value = self.value
            obj = value.to_object

            return rdflib.URIRef(obj.absolute_url())
