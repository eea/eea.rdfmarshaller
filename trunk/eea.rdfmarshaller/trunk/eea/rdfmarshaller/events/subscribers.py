""" event subscribers
"""
import logging
import urllib2
import urllib
import lxml.etree

from zope.component import getUtility, queryUtility
from plone.registry.interfaces import IRegistry
from plone.app.async.interfaces import IAsyncService

hasLinguaPloneInstalled = True
try:
    from Products.LinguaPlone.interfaces import ITranslatable
except ImportError:
    hasLinguaPloneInstalled = False

from eea.rdfmarshaller.controlpanel.interfaces import IRDFMarshallerSettings

hasVersionsInstalled = True
try:
    from eea.versions.interfaces import IGetVersions, IVersionEnhanced
except ImportError:
    hasVersionsInstalled = False

logger = logging.getLogger("eea.rdfmarshaller")

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
            logger.info("Pinging %s for object %s with create=%s" \
                % (options['service_to_ping'], 
                    options['obj_url'], 
                    options['create']))
            ping_con = urllib2.urlopen(url)
            ping_response = ping_con.read()
            ping_con.close()
            response = lxml.etree.fromstring(ping_response)
            message = response.find("message").text
            logger.info("Response for pinging %s for object %s: %s" \
                % (options['service_to_ping'],
                    options['obj_url'],
                    message))
            if (not options['create']) and \
                message == 'URL not in catalogue of sources, no action taken.':
                logger.info("Retry ping with create=true")
                options['create'] = True
                continue
        except urllib2.HTTPError, err:
            logger.info("Pinging %s for object %s failed with message: %s" \
                % (options['service_to_ping'],
                    options['obj_url'],
                    err.msg))

        break


def schedule_ping_CRSDS(context, create):
    """ generic event
    """
    registry = queryUtility(IRegistry)
    if not registry:
        return

    settings = registry.forInterface(IRDFMarshallerSettings, False)
    if not settings:
        return
    if not settings.services_to_ping:
        return

    if hasLinguaPloneInstalled and ITranslatable.providedBy(context):
        context = context.getCanonical()

    if hasVersionsInstalled and IVersionEnhanced.providedBy(context):
        obj_versions = IGetVersions(context).versions()
    else:
        obj_versions = [context]

    async = getUtility(IAsyncService)
    for service_to_ping in settings.services_to_ping:
        for obj in obj_versions:
            obj_url = "%s/@@rdf" % obj.absolute_url()
            options = {}
            options['service_to_ping'] = service_to_ping
            options['obj_url'] = obj_url
            options['create'] = create
            async.queueJob(ping_CRSDS, context, options)

def schedule_ping_CRSDS_created(context, evt):
    """ created event
    """
    schedule_ping_CRSDS(context, True)

def schedule_ping_CRSDS_modified(context, evt):
    """ modified event
    """
    schedule_ping_CRSDS(context, False)
