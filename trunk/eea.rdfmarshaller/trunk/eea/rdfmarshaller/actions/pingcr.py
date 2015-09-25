""" RDF Marshaller ping action
"""
import logging
import urllib2
import urllib
import lxml.etree
from App.config import getConfiguration
from zope import schema
from zope.component import adapts, getUtility, ComponentLookupError
from zope.formlib import form
from zope.interface import implements, Interface
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from OFS.SimpleItem import SimpleItem
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from plone.app.async.interfaces import IAsyncService
from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from eea.rdfmarshaller.actions.interfaces import IObjectMovedOrRenamedEvent

hasLinguaPloneInstalled = True
try:
    from Products.LinguaPlone.interfaces import ITranslatable
except ImportError:
    hasLinguaPloneInstalled = False

hasVersionsInstalled = True
try:
    from eea.versions.interfaces import IGetVersions, IVersionEnhanced
except ImportError:
    hasVersionsInstalled = False

logger = logging.getLogger("eea.rdfmarshaller")


class IPingCRAction(Interface):
    """ Ping action settings schema
    """
    service_to_ping = schema.TextLine(title=u"Service to ping",
                              description=u"Service to ping.",
                              required=True)


class PingCRAction(SimpleItem):
    """ Ping action settings
    """
    implements(IPingCRAction, IRuleElementData)

    service_to_ping = ''

    element = 'eea.rdfmarshaller.actions.PingCR'

    summary = u'ping cr'


class PingCRActionExecutor(object):
    """ Ping action executor
    """
    implements(IExecutable)
    adapts(Interface, IPingCRAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        event = self.event
        service_to_ping = self.element.service_to_ping
        obj = self.event.object
        container = obj.getParentNode()
        noasync_msg = 'No instance for async operations was defined.'

        def pingCRSDS(service_to_ping, obj_url, create):
            """ Ping the CR/SDS service
            """
            options = {}
            options['service_to_ping'] = service_to_ping
            options['obj_url'] = self.sanitize_url(obj_url)
            options['create'] = create
            try:
                async.queueJob(ping_CRSDS, self.context, options)
            except ComponentLookupError:
                logger.info(noasync_msg)

        def pingCRSDS_backrel(service_to_ping, obj, create):
            """ Ping backward relations
            """
            back_relations = obj.getBRefs('relatesTo')
            for rel in back_relations:
                obj_url = "%s/@@rdf" % rel.absolute_url()
                pingCRSDS(service_to_ping, obj_url, create)

        def pingCRSDS_children(service_to_ping, obj, create):
            """ Ping all sub-objects
            """
            if obj.portal_type == "Discussion Item":
                # 22047 skip object if it's of type Discussion Item
                return
            for child in obj.objectIds():
                child_obj = obj.get(child)
                if not child_obj:
                    logger.info("Couldn't retrieve child id %s for %s",
                        child, obj.absolute_url())
                    continue
                obj_url = "%s/@@rdf" % child_obj.absolute_url()
                pingCRSDS(service_to_ping, obj_url, create)
                pingCRSDS_children(service_to_ping, child_obj, create)


        # When no request the task is called from a async task, see #19830
        request = getattr(obj, 'REQUEST', None)

        # Detect special object used to force acquisition, see #18904
        if isinstance(request, str):
            request = None

        create = IObjectAddedEvent.providedBy(event)

        if service_to_ping == "":
            return

        if hasVersionsInstalled and IVersionEnhanced.providedBy(obj) \
                                                              and request:
            obj_versions = IGetVersions(obj).versions()
        else:
            obj_versions = [obj]

        async = getUtility(IAsyncService)

        # If object has translations
        if hasLinguaPloneInstalled and ITranslatable.providedBy(obj):
            if obj.isCanonical():
                # Ping all translations
                for trans in obj.getTranslations().items():
                    if trans[0] != 'en':
                        trans_obj = trans[1][0]
                        obj_url = trans_obj.absolute_url()
                        pingCRSDS(service_to_ping, obj_url, create)
            else:
                # Ping only canonical
                can_obj = obj.getCanonical()
                obj_url = can_obj.absolute_url()
                pingCRSDS(service_to_ping, obj_url, create)

        # If object was deleted
        if IObjectRemovedEvent.providedBy(event):
            # Ping backward relations
            pingCRSDS_backrel(service_to_ping, obj, create)

            # Ping all sub-objects
            pingCRSDS_children(service_to_ping, obj, create)

        # If object was moved/renamed first ping with the old object's URL
        if IObjectMovedOrRenamedEvent.providedBy(event):
            obj_url = "%s/%s/@@rdf" % (event.oldParent.absolute_url(), \
                                       event.oldName)
            pingCRSDS(service_to_ping, obj_url, False)

            # then ping with the container of the old object
            obj_url = "%s/@@rdf" % event.oldParent.absolute_url()
            pingCRSDS(service_to_ping, obj_url, False)

            # Ping backward relations
            pingCRSDS_backrel(service_to_ping, obj, create)

            # Ping all sub-objects
            pingCRSDS_children(service_to_ping, obj, create)

        # Ping each version
        for obj in obj_versions:
            obj_url = "%s/@@rdf" % obj.absolute_url()
            pingCRSDS(service_to_ping, obj_url, create)

        # If no Aquisition there is no container, see #18904
        if container:
            obj_url = "%s/@@rdf" % container.absolute_url()
            pingCRSDS(service_to_ping, obj_url, False)

        return True

    def sanitize_url(self, url):
        """ Replace object's portal_url value with the one defined as an
            environment value if any
        """
        portal_url_tool = getToolByName(self.context, 'portal_url')
        portal_url = portal_url_tool()
        conf = getConfiguration()

        if not hasattr(conf, 'environment'):
            return  # this happens during unit tests, we skip this procedure

        default_url = conf.environment.get('portal_url', portal_url)

        if default_url != portal_url:
            url = url.replace(unicode(portal_url), unicode(default_url))
            url = url.replace('SITE/', '')

        return url

class PingCRAddForm(AddForm):
    """ Ping action addform
    """
    form_fields = form.FormFields(IPingCRAction)
    label = u"Add Ping CR Action"
    description = u"A ping CR action."
    form_name = u"Configure element"

    def create(self, data):
        """ Ping action create method
        """
        a = PingCRAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class PingCREditForm(EditForm):
    """ Ping action editform
    """
    form_fields = form.FormFields(IPingCRAction)
    label = u"Edit Ping CR Action"
    description = u"A ping cr action."
    form_name = u"Configure element"


class PingCRView(BrowserView):
    """ Ping CR/SDS View
    """
    def __call__(self, url, **kwargs):
        context = self.context
        options = {}
        options['create'] = False
        options['service_to_ping'] = 'http://semantic.eea.europa.eu/ping'
        options['obj_url'] = url
        ping_CRSDS(context, options)

def ping_CRSDS(context, options):
    """ Ping the CR/SDS service
    """
    while True:
        try:
            params = {}
            params['uri'] = options['obj_url']
            if options['create']:
                params['create'] = options['create']
            encoded_params = urllib.urlencode(params)
            url = "%s?%s" % (options['service_to_ping'], encoded_params)
            logger.info("Pinging %s for object %s with create=%s",
                    options['service_to_ping'],
                    options['obj_url'],
                    options['create'])
            ping_con = urllib2.urlopen(url, timeout=10)
            ping_response = ping_con.read()
            ping_con.close()
            response = lxml.etree.fromstring(ping_response)
            try:
                message = response.find("message").text
                logger.info("Response for pinging %s for object %s: %s",
                        options['service_to_ping'],
                        options['obj_url'],
                        message)
            except AttributeError:
                message = 'no message'
                logger.info("Pinging %s for object %s failed without message",
                        options['service_to_ping'],
                        options['obj_url'])
            if (not options['create']) and \
                message == 'URL not in catalogue of sources, no action taken.':
                logger.info("Retry ping with create=true")
                options['create'] = True
                continue
        except urllib2.HTTPError, err:
            logger.info("Pinging %s for object %s failed with message: %s",
                    options['service_to_ping'],
                    options['obj_url'],
                    err.msg)

        break
