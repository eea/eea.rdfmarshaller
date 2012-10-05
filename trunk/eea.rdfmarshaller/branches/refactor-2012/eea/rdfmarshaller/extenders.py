def add_translation_info(context, resource):
    """Add info about translations
    """
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


