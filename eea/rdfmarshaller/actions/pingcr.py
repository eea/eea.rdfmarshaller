""" RDF Marshaller ping action
"""
import logging
import pytz
import urllib
import lxml.etree
from eventlet.green import urllib2
from datetime import datetime, timedelta
from zope import schema
from zope.interface import implementer, Interface
from zope.component import adapts, queryUtility, ComponentLookupError
from zope.formlib import form
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from App.config import getConfiguration
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
try:
    from Products.LinguaPlone.interfaces import ITranslatable
    hasLinguaPloneInstalled = True
except ImportError:
    hasLinguaPloneInstalled = False
from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from eea.rabbitmq.plone.rabbitmq import get_rabbitmq_client_settings
from eea.rabbitmq.plone.rabbitmq import queue_msg
from eea.rdfmarshaller.asyncode import IAsyncService
from eea.rdfmarshaller.actions.interfaces import IObjectMovedOrRenamedEvent
try:
    from eea.versions.interfaces import IGetVersions, IVersionEnhanced
    hasVersionsInstalled = True
except ImportError:
    hasVersionsInstalled = False

logger = logging.getLogger("eea.rdfmarshaller")


class IPingCRAction(Interface):
    """ Ping action settings schema
    """
    service_to_ping = schema.TextLine(
        title=u"Service to ping",
        description=u"Service to ping.",
        required=True
    )


@implementer(IPingCRAction, IRuleElementData)
class PingCRAction(SimpleItem):
    """ Ping action settings
    """

    service_to_ping = ''

    element = 'eea.rdfmarshaller.actions.PingCR'

    summary = u'ping cr'


@implementer(IExecutable)
class PingCRActionExecutor(object):
    """ Ping action executor
    """
    adapts(Interface, IPingCRAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event
        self._rabbit_config = None

    @property
    def rabbit_config(self):
        """ RabbitMQ Config
        """
        if self._rabbit_config is not None:
            return self._rabbit_config

        try:
            self._rabbit_config = get_rabbitmq_client_settings()
        except Exception:
            self._rabbit_config = {}
        return self._rabbit_config

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

            # Use RabbitMQ if available
            if self.rabbit_config:
                options['create'] = 'create' if options.get(
                    'create', False) else 'update'
                return ping_RabbitMQ(options)

            # Use zc.async if available
            if async_service is None:
                logger.warn("Can't pingCRSDS, plone.app.async not installed!")
                return

            queue = async_service.getQueues()['']
            try:
                async_service.queueJobInQueue(
                    queue, ('rdf',),
                    ping_CRSDS, self.context, options
                )
            except ComponentLookupError:
                logger.info(noasync_msg)

        def pingCRSDS_backrel(service_to_ping, obj, create):
            """ Ping backward relations
            """
            if hasattr(obj, 'getBRefs'):
                back_relations = obj.getBRefs('relatesTo')
            else:
                back_relations = [o.to_object
                    for o in getattr(obj, 'relatedItems')
                ]

            for rel in back_relations:
                if rel is not None:
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
                    logger.info(
                        "Couldn't retrieve child id %s for %s",
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

        async_service = queryUtility(IAsyncService)

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
            obj_url = "%s/%s/@@rdf" % (event.oldParent.absolute_url(),
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

        # Force ping_cr on HTTP to fit Virtuoso triples
        default_url = default_url.replace('https://', 'http://', 1)

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


def ping_RabbitMQ(options):
    """ Ping the CR/SDS service via RabbitMQ
    """
    msg = "{create}|{service_to_ping}|{obj_url}".format(**options)
    try:
        queue_msg(msg, queue="sds_queue")
    except Exception as err:
        logger.error("Sending '%s' in 'sds_queue' FAILED: %s", msg, err)


def ping_CRSDS(context, options):
    """ Ping the CR/SDS service via zc.async
    """
    while True:
        try:
            params = {}
            params['uri'] = options['obj_url']
            if options['create']:
                params['create'] = options['create']
            encoded_params = urllib.urlencode(params)
            url = "%s?%s" % (options['service_to_ping'], encoded_params)
            logger.info(
                "Pinging %s for object %s with create=%s",
                options['service_to_ping'],
                options['obj_url'],
                options['create'])
            ping_con = urllib2.urlopen(url, timeout=10)
            ping_response = ping_con.read()
            ping_con.close()
            response = lxml.etree.fromstring(ping_response)

            try:
                message = response.find("message").text
                logger.info(
                    "Response for pinging %s for object %s: %s",
                    options['service_to_ping'],
                    options['obj_url'],
                    message)
            except AttributeError:
                message = 'no message'

            if (not options['create']) and \
               'URL not in catalogue of sources' in message:
                #Retry ping with create=true
                options['create'] = True
                continue
        except Exception as err:
            # re-schedule PING on error
            schedule = datetime.now(pytz.UTC) + timedelta(hours=4)
            async_service = queryUtility(IAsyncService)
            queue = async_service.getQueues()['']
            async_service.queueJobInQueueWithDelay(
                None, schedule, queue, ('rdf',),
                ping_CRSDS, context, options
            )

            # mark the original job as failed
            return "Ping re-scheduled as pinging %s for object %s failed. "\
                   "Reason: %s " % (
                       options['service_to_ping'],
                       options['obj_url'],
                       str(err))

        break
