""" Archetypes modifiers
"""
from Acquisition import aq_inner
from Products.Archetypes.interfaces import IBaseContent
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from eea.rdfmarshaller.interfaces import ISurfResourceModifier
from zope.component import adapts
from zope.interface import implements, providedBy
import rdflib
import re

ILLEGAL_XML_CHARS_PATTERN = re.compile(
    u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]'
)

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
                #object has no workflow, we assume public, see #4418
                state = 'published'

            if state == 'published':
                parent_url = parent.absolute_url()
                resource.dcterms_isPartOf = \
                    rdflib.URIRef(parent_url) #pylint: disable = W0612


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

        #ZZZ: should watch for availability of Products.LinguaPlone

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

        resource.dcterms_abstract = ILLEGAL_XML_CHARS_PATTERN.sub('',
            self.context.SearchableText())

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

        resource.dcterms_references = [rdflib.URIRef(o.absolute_url()) \
            for o in self.context.getRelatedItems()]
