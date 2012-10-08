class IsPartOfModifier(object):
    """Adds dcterms_isPartOf information to rdf resources
    """

    implements(ISurfModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource):
        """Change the rdf resource
        """
        parent = getattr(aq_inner(self.context), 'aq_parent', None)
        wftool = getToolByName(self.context, 'portal_workflow')
        if (parent is not None):
            try:
                state = wftool.getInfoFor(parent, 'review_state')
            except WorkflowException:
                #object has no workflow, we assume public, see #4418
                state = 'published'

            if state == 'published':
                parent_url = parent.absolute_url()
                rdf.dcterms_isPartOf = \
                    rdflib.URIRef(parent_url) #pylint: disable-msg = W0612


class TranslationInfoModifier(object):
    """Adds translation info 
    """

    implements(ISurfModifier)
    adapts(IBaseContent)

    def __init__(self, context):
        self.context = context

    def run(self, resource):
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
                    if o.absolute_url()!=context.absolute_url()]
        else:
            resource.eea_isTranslationOf = \
                rdflib.URIRef( context.getCanonical().absolute_url())

