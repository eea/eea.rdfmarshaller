class Archetype2Surf(GenericObject2Surf):
    """IArchetype2Surf implementation for AT based content items"""

    implements(IArchetype2Surf)
    adapts(IBaseContent, ISurfSession)

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

    def update_resource(self, resource, *args, **kwds):
        """ Schema to Surf """
        language = self.context.Language()

        for field in self.context.Schema().fields():

            fieldName = field.getName()
            if fieldName in self.blacklist_map:
                continue

            fieldAdapter = queryMultiAdapter((field, self.context, self.session),
                                              interface=IATField2Surf)
            if not fieldAdapter.exportable:
                continue

            value = fieldAdapter.value(self.context)
            valueAdapter = queryAdapter(value, interface="IValue2Surf")
            if valueAdapter:
                value = valueAdapter()
            if not value or value == "None":
                continue

            prefix = self.prefix
            if fieldName in self.field_map:
                fieldName = self.field_map.get(fieldName)
            elif fieldName in self.dc_map:
                fieldName = self.dc_map.get(fieldName)
                prefix = 'dcterms'

            setattr(resource, '%s_%s' % (prefix, fieldName), value)

        return resource


class ATVocabularyTerm2Surf(Archetype2Surf):
    """IArchetype2Surf implemention for ATVocabularyTerms"""

    implements(IArchetype2Surf)
    adapts(IATVocabularyTerm, ISurfSession)

    @property
    def blacklist_map(self):
        """ Blacklist map """
        return super(ATVocabularyTerm2Surf, self).blacklist_map + \
                ['creation_date', 'modification_date', 'creators']


class ATFolderish2Surf(Archetype2Surf):
    """IArchetype2Surf implemention for Folders"""

    implements(IArchetype2Surf)
    adapts(IFolder, ISurfSession)

    def update_resource(self, resource, currentLevel=0, endLevel=1, **kwargs):
        """ AT to Surf """
        currentLevel += 1
        resource = super(ATFolderish2Surf, self).update_resource(
                         currentLevel=currentLevel, endLevel=endLevel)
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


class ATField2RdfSchema(GenericObject2Surf):
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

    def update_resource(self, resource, *args, **kwargs):
        """ Schema to Surf """
        context = self.context

        widget_label = (context.widget.label, u'en')
        widget_description = (context.widget.description, u'en')
        fti_title = rdflib.URIRef(u'#%s' % self.fti.Title())

        setattr(resource, 'rdfs_label', widget_label)
        setattr(resource, 'rdfs_comment', widget_description)
        setattr(resource, 'rdf_id', self.rdfId)
        setattr(resource, 'rdf_domain', fti_title)
        return resource
