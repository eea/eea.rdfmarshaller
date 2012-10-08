class Archetype2Surf(GenericObject2Surf):
    """IArchetype2Surf implementation for AT based content items"""

    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)

    dc_map = dict([('title', 'title'),
                   ('description', 'description'),
                   ('creation_date', 'created'),
                   ('modification_date', 'modified'),
                   ('creators', 'creator'),
                   ('subject', 'subject'),
                   ('effectiveDate', 'issued'),
                   ('expirationDate', 'expires'),
                   ('rights', 'rights'),
                   ])

    _blacklist = [   'constrainTypesMode', 
                     'locallyAllowedTypes',
                     'immediatelyAddableTypes',
                     'language',
                     'allowDiscussion']
    field_map = {}

    @property
    def blacklist_map(self):
        """ These fields shouldn't be exported """
        ptool = getToolByName(self.context,'portal_properties')
        props = getattr(ptool, 'rdfmarshaller_properties', None)
        if props:
            return list(props.getProperty('%s_blacklist' %
                self.portalType.lower(), props.getProperty('blacklist')))
        else:
                return self._blacklist

    @property
    def subject(self):
        """ Subject """
        return self.context.absolute_url()

    def update_resource(self, resource):
        """ Schema to Surf """
        language = self.context.Language()

        add_translation_info(self.context, resource)

        for field in self.context.Schema().fields():
            fieldName = field.getName()
            if fieldName in self.blacklist_map:
                continue
            fieldAdapter = queryMultiAdapter((field, self.context, self.session),
                                              interface=IATField2Surf)

            if fieldAdapter.exportable:
                try:
                    value = fieldAdapter.value(self.context)
                except TypeError:
                    if DEBUG:
                        raise
                    log.log('RDF marshaller error for context[field]'
                            ' "%s[%s]": \n%s: %s' %
                            (self.context.absolute_url(), fieldName,
                             sys.exc_info()[0], sys.exc_info()[1]),
                             severity=log.logging.WARN)
                    continue

                valueAdapter = queryAdapter(value, interface="IValue2Surf")
                if valueAdapter:
                    value = valueAdapter()

                #this logic should be refactored
                if (value and value != "None"):

                    prefix = self.prefix
                    if fieldName in self.field_map:
                        fieldName = self.field_map.get(fieldName)
                    elif fieldName in self.dc_map:
                        fieldName = self.dc_map.get(fieldName)
                        prefix = 'dcterms'

                    try:
                        setattr(resource, '%s_%s' % (prefix, fieldName), value)
                    except Exception:
                        if DEBUG:
                            raise
                        log.log('RDF marshaller error for context[field]'
                                '"%s[%s]": \n%s: %s' %
                                (self.context.absolute_url(), fieldName,
                                 sys.exc_info()[0], sys.exc_info()[1]),
                                 severity=log.logging.WARN)

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
                resource.dcterms_isPartOf = \
                    rdflib.URIRef(parent_url) #pylint: disable-msg = W0612

        #resource.save()
        return resource

    #def at2surf(self, currentLevel=0, endLevel=1, **kwargs):
        #""" AT to Surf """

        #res = self._schema2surf() 

        #for modifier in subscribers([self.context], ISurfResourceModifier):
            #modifier.run(res)
        #return res


class ATVocabularyTerm2Surf(Archetype2Surf):
    """IArchetype2Surf implemention for ATVocabularyTerms"""

    implements(IArchetype2Surf)
    adapts(IATVocabularyTerm, ISurfSession)

    @property
    def blacklist_map(self):
        """ Blacklist map """
        return super(ATVocabularyTerm2Surf, self).blacklist_map + \
                ['creation_date', 'modification_date', 'creators']


class ATFolderish2Surf(ATCT2Surf):
    """IArchetype2Surf implemention for Folders"""

    implements(IArchetype2Surf)
    adapts(IFolder, ISurfSession)

    def at2surf(self, currentLevel=0, endLevel=1, **kwargs):
        """ AT to Surf """
        currentLevel += 1
        resource = super(ATFolderish2Surf, self).at2surf(
                currentLevel=currentLevel, endLevel=endLevel)
        add_translation_info(self.context, resource)
        if currentLevel <= endLevel or endLevel == 0:
            resource.dcterms_hasPart = []

            objs = [b.getObject() for b in self.context.getFolderContents()]
                    #contentFilter={'review_state':'published'})]

            for obj in objs:
                resource.dcterms_hasPart.append(rdflib.URIRef(
                                                    obj.absolute_url()))
                atsurf = queryMultiAdapter((obj, self.session),
                                            interface=IArchetype2Surf)
                if atsurf is not None:
                    self.session.default_store.reader.graph.bind(
                            atsurf.prefix, atsurf.namespace, override=False)
                    atsurf.at2surf(currentLevel=currentLevel, endLevel=endLevel)
        resource.save()
        return resource


class ATField2RdfSchema(ATCT2Surf):
    """IArchetype2Surf implemention for Fields"""

    implements(IArchetype2Surf)
    adapts(IField, Interface, ISurfSession)

    def __init__(self, context, fti, session):
        super(ATField2RdfSchema, self).__init__(context, session)
        self.fti = fti

    @property
    def portalType(self):
        """ portal type """
        return u'Property'

    @property
    def namespace(self):
        """ namespace """
        return surf.ns.RDFS

    @property
    def prefix(self):
        """ prefix """
        return 'rdfs'

    @property
    def rdfId(self):
        """ rdf id """
        return self.context.getName().replace(' ','')

    @property
    def subject(self):
        """ subject """
        return '%s#%s' % (self.fti.absolute_url(), self.context.getName())

    def _schema2surf(self):
        """ Schema to Surf """
        context = self.context
        resource = self.surfResource

        widget_label = (context.widget.label, u'en')
        widget_description = (context.widget.description, u'en')
        fti_title = rdflib.URIRef(u'#%s' % self.fti.Title())

        setattr(resource, 'rdfs_label', widget_label)
        setattr(resource, 'rdfs_comment', widget_description)
        setattr(resource, 'rdf_id', self.rdfId)
        setattr(resource, 'rdf_domain', fti_title)
        resource.save()
        return resource
