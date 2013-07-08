""" RDF Marshaller ping action
"""
import logging
import urllib2
import urllib
import lxml.etree

from zope import schema
from zope.component import adapts, getUtility
from zope.formlib import form
from zope.interface import implements, Interface
from zope.lifecycleevent.interfaces import IObjectAddedEvent

from OFS.SimpleItem import SimpleItem

from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from plone.app.async.interfaces import IAsyncService
from plone.app.contentrules.browser.formhelper import AddForm, EditForm

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
    """ Ping Action settings schema
    """
    service_to_ping = schema.TextLine(title=u"Service to ping",
                              description=u"Service to ping.",
                              required=True)



class PingCRAction(SimpleItem):
    """ Ping Action settings
    """
    implements(IPingCRAction, IRuleElementData)

    service_to_ping = ''

    element = 'eea.rdfmarshaller.actions.PingCR'

    summary = u'ping cr'


class PingCRActionExecutor(object):
    """ Ping Action executor
    """
    implements(IExecutable)
    adapts(Interface, IPingCRAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        container = self.context
        event = self.event
        service_to_ping = self.element.service_to_ping
        obj = self.event.object

        create = IObjectAddedEvent.providedBy(event)

        if service_to_ping == "":
            return

        if hasLinguaPloneInstalled and ITranslatable.providedBy(obj):
            obj = obj.getCanonical()

        if hasVersionsInstalled and IVersionEnhanced.providedBy(obj):
            obj_versions = IGetVersions(obj).versions()
        else:
            obj_versions = [obj]

        async = getUtility(IAsyncService)

        for obj in obj_versions:
            obj_url = "%s/@@rdf" % obj.absolute_url()
            options = {}
            options['service_to_ping'] = service_to_ping
            options['obj_url'] = obj_url
            options['create'] = create
            async.queueJob(ping_CRSDS, self.context, options)

        if create:
            obj_url = "%s/@@rdf" % container.absolute_url()
            options = {}
            options['service_to_ping'] = service_to_ping
            options['obj_url'] = obj_url
            options['create'] = False
            async.queueJob(ping_CRSDS, self.context, options)

        return True


class PingCRAddForm(AddForm):
    """ Ping Action addform
    """
    form_fields = form.FormFields(IPingCRAction)
    label = u"Add Ping CR Action"
    description = u"A ping CR action."
    form_name = u"Configure element"

    def create(self, data):
        """ Ping Action Create method
        """
        a = PingCRAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class PingCREditForm(EditForm):
    """ Ping Action editform
    """
    form_fields = form.FormFields(IPingCRAction)
    label = u"Edit Ping CR Action"
    description = u"A ping cr action."
    form_name = u"Configure element"


def ping_CRSDS(context, options):
    """ ping the CR/SDS service
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
            ping_con = urllib2.urlopen(url)
            ping_response = ping_con.read()
            ping_con.close()
            response = lxml.etree.fromstring(ping_response)
            message = response.find("message").text
            logger.info("Response for pinging %s for object %s: %s", 
                    options['service_to_ping'],
                    options['obj_url'],
                    message)
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
