""" Archetypes modifiers
"""

import re
import sys

import rdflib
from Acquisition import aq_inner
from eea.rdfmarshaller.archetypes.interfaces import IATField2Surf
from eea.rdfmarshaller.interfaces import ISurfResourceModifier, IValue2Surf
from Products.Archetypes.interfaces import IBaseContent, IBaseObject
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone import log
from zope.component import (adapts, getMultiAdapter, queryAdapter,
                            queryMultiAdapter)
from zope.interface import implements, providedBy

ILLEGAL_XML_CHARS_PATTERN = re.compile(
    u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]'
)


class FieldsModifier(object):
    """ Adds archetypes fields values to rdf
    """
    implements(ISurfResourceModifier)
    adapts(IBaseObject)

    def __init__(self, context):
        self.context = context

    def run(self, resource, adapter, session, *args, **kwds):
        """ modifier run method """
        language = self.context.Language()

        for field in self.context.Schema().fields():
            fieldName = field.getName()

            if fieldName in adapter.blacklist_map:
                continue

            # first we try with a named adapter, then a generic one
            fieldAdapter = queryMultiAdapter((field, self.context, session),
                                             interface=IATField2Surf,
                                             name=fieldName)

            if not fieldAdapter:
                fieldAdapter = getMultiAdapter((field, self.context, session),
                                               interface=IATField2Surf)

            if not fieldAdapter.exportable:
                continue

            try:
                value = fieldAdapter.value()
            except Exception:
                log.log('RDF marshaller error for context[field]'
                        '"%s[%s]": \n%s: %s' %
                        (self.context.absolute_url(), fieldName,
                         sys.exc_info()[0], sys.exc_info()[1]),
                        severity=log.logging.WARN)

            valueAdapter = queryAdapter(value, interface=IValue2Surf)

            if valueAdapter:
                value = valueAdapter(language=language)

            if not value or value == "None":
                continue

            prefix = fieldAdapter.prefix or adapter.prefix

            if fieldAdapter.name:
                fieldName = fieldAdapter.name
            elif fieldName in adapter.field_map:
                fieldName = adapter.field_map.get(fieldName)
            elif fieldName in adapter.dc_map:
                fieldName = adapter.dc_map.get(fieldName)
                prefix = 'dcterms'

            try:
                setattr(resource, '%s_%s' % (prefix, fieldName), value)
            except Exception:

                log.log('RDF marshaller error for context[field]'
                        '"%s[%s]": \n%s: %s' %
                        (self.context.absolute_url(), fieldName,
                         sys.exc_info()[0], sys.exc_info()[1]),
                        severity=log.logging.WARN)

        return resource


class IsPartOfModifier(object):
    """Adds dcterms_isPartOf information to rdf resources
    """

    implements(ISurfResourceModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """Change the rdf resource
        """
        parent = getattr(aq_inner(self.context), 'aq_parent', None)
        wftool = getToolByName(self.context, 'portal_workflow')

        if parent is not None:
            try:
                state = wftool.getInfoFor(parent, 'review_state')
            except WorkflowException:
                # object has no workflow, we assume public, see #4418
                state = 'published'

            if state == 'published':
                parent_url = parent.absolute_url()
                resource.dcterms_isPartOf = \
                    rdflib.URIRef(parent_url)   # pylint: disable = W0612


class TranslationInfoModifier(object):
    """Adds translation info
    """

    implements(ISurfResourceModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """Change the rdf resource
        """

        context = self.context

        # ZZZ: should watch for availability of Products.LinguaPlone

        if not getattr(context, 'isCanonical', None):
            return

        if context.isCanonical():
            translations = context.getTranslations(review_state=False)
            resource.eea_hasTranslation = \
                [rdflib.URIRef(o.absolute_url()) for o in translations.values()
                 if o.absolute_url() != context.absolute_url()]
        else:
            resource.eea_isTranslationOf = \
                rdflib.URIRef(context.getCanonical().absolute_url())


class ProvidedInterfacesModifier(object):
    """Adds information about provided interfaces
    """

    implements(ISurfResourceModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """Change the rdf resource
        """
        provides = ["%s.%s" % (iface.__module__ or '', iface.__name__)
                    for iface in providedBy(self.context)]

        resource.eea_objectProvides = provides


class SearchableTextInModifier(object):
    """Adds searchable text info
    """

    implements(ISurfResourceModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """Change the rdf resource
        """

        resource.dcterms_abstract = ILLEGAL_XML_CHARS_PATTERN.sub(
            '', self.context.SearchableText())


class RelatedItemsModifier(object):
    """Adds dcterms:references
    """

    implements(ISurfResourceModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """Change the rdf resource
        """

        if not getattr(self.context, 'getRelatedItems', None):
            return

        resource.dcterms_references = [rdflib.URIRef(o.absolute_url())
                                       for o in self.context.getRelatedItems()]
