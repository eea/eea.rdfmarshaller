class ATCTDublinCore2Surf(object):
    """Base implementation of IArchetype2Surf 
    
    comment: is this used anywhere?
    """
    implements(IArchetype2Surf)
    adapts(Interface, ISurfSession)

    def __init__(self, context, session):
        self.context = context
        self.session = session


class ATField2Surf(object):
    """Base implementation of IATField2Surf
    
    ZZZ: this should be refactored to take the real content into account
    """

    implements(IATField2Surf)
    adapts(IField, ISurfSession)

    exportable = True

    def __init__(self, context, session):
        self.field = context
        self.session = session

    def value(self, context):
        """ Value """
        return self.field.getAccessor(context)()


class ATFileField2Surf(ATField2Surf):
    """IATField2Surf implementation for File fields"""
    implements(IATField2Surf)
    adapts(IFileField, ISurfSession)

    exportable = False


class ATReferenceField2Surf(ATField2Surf):
    """IATField2Surf implementation for Reference fields"""
    implements(IATField2Surf)
    adapts(IReferenceField, ISurfSession)

    def value(self, context):
        """ Value """
        value = self.field.getAccessor(context)()

        #some reference fields are single value only
        if not isinstance(value, (list, tuple)):
            value = [value]

        value = [v for v in value if v] #the field might have been empty

        return [ rdflib.URIRef(obj.absolute_url()) for obj in value ]


class ATCT2Surf(object):
    """IArchetype2Surf implementation for ATCT"""

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

    field_map = {}

    def __init__(self, context, session):
        self.context = context
        self.session = session
        if self.namespace is None:
            ttool = getToolByName(context, 'portal_types')
            surf.ns.register(**{ self.prefix : '%s#' %
                                 ttool[context.portal_type].absolute_url()} )

    @property
    def blacklist_map(self):
        """ Blacklist map """
        ptool = getToolByName(self.context,'portal_properties')
        props = getattr(ptool, 'rdfmarshaller_properties', None)
        # fields not to export
        blacklist = ['constrainTypesMode',
                     'locallyAllowedTypes',
                     'immediatelyAddableTypes',
                     'language',
                     'allowDiscussion']
        if props:
            blacklist = list(props.getProperty('%s_blacklist' %
                self.portalType.lower(), props.getProperty('blacklist')))
        return blacklist

    @property
    def namespace(self):
        """ Namespace """
        return getattr(surf.ns, self.prefix.upper(), None)

    @property
    def prefix(self):
        """ Prefix """
        return self.portalType.lower()

    @property
    def portalType(self):
        """ Portal type """
        return self.context.portal_type.replace(' ','')

    @property
    def surfResource(self):
        """ Surf resource """
        try:
            resource = self.session.get_class(
                self.namespace[self.portalType])(self.subject)
        except Exception:
            if DEBUG:
                raise
            log.log('RDF marshaller error \n%s: %s' %
                    (sys.exc_info()[0], sys.exc_info()[1]),
                    severity=log.logging.WARN)
            return None

        resource.bind_namespaces([self.prefix])
        resource.session = self.session
        return resource

    @property
    def subject(self):
        """ Subject """
        return self.context.absolute_url()

    def _schema2surf(self):
        """ Schema to Surf """
        context = self.context
        #session = self.session
        resource = self.surfResource
        language = context.Language()

        add_translation_info(self.context, resource)

        for field in context.Schema().fields():
            fieldName = field.getName()
            if fieldName in self.blacklist_map:
                continue
            fieldAdapter = queryMultiAdapter((field, self.session),
                    interface=IATField2Surf)

            if fieldAdapter.exportable:
                try:
                    value = fieldAdapter.value(context)
                except TypeError:
                    if DEBUG:
                        raise
                    log.log('RDF marshaller error for context[field]'
                            ' "%s[%s]": \n%s: %s' %
                            (context.absolute_url(), fieldName,
                             sys.exc_info()[0], sys.exc_info()[1]),
                             severity=log.logging.WARN)
                    continue

                if (value and value != "None") or \
                        (isinstance(value, basestring) and value.strip()) :

                    if isinstance(value, (list, tuple)):
                        value = list(value)
                    elif isinstance(value, DateTime):
                        value = (value.HTML4(), None,
                                'http://www.w3.org/2001/XMLSchema#dateTime')
                    elif isinstance(value, str):
                        encoding = detect(value)['encoding']
                        try:
                            value = value.decode(encoding)
                        except (LookupError, UnicodeDecodeError):
                            log.log("Could not decode to %s in rdfmarshaller" % 
                                     encoding)
                            value = value.decode('utf-8','replace')
                        value = (value.encode('utf-8'), language)
                    elif isinstance(value, unicode):
                        pass
                    else:
                        try:
                            value = (unicode(value, 'utf-8', 'replace'),
                                    language)
                        except TypeError:
                            value = str(value)

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
                                (context.absolute_url(), fieldName,
                                 sys.exc_info()[0], sys.exc_info()[1]),
                                 severity=log.logging.WARN)

        parent = getattr(aq_inner(context), 'aq_parent', None)
        wftool = getToolByName(context, 'portal_workflow')
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

        resource.save()
        return resource

    def at2surf(self, currentLevel=0, endLevel=1, **kwargs):
        """ AT to Surf """

        res = self._schema2surf() 

        for modifier in subscribers([self.context], ISurfResourceModifier):
            modifier.run(res)
        return res


class ATVocabularyTerm2Surf(ATCT2Surf):
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
