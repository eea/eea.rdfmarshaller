""" event subscribers
"""
import logging
import urllib2
import urllib

from zope.component import getUtility, queryUtility
from plone.registry.interfaces import IRegistry
from plone.app.async.interfaces import IAsyncService

from eea.rdfmarshaller.controlpanel.interfaces import IRDFMarshallerSettings
from eea.versions.interfaces import IGetVersions, IVersionEnhanced

logger = logging.getLogger("eea.rdfmarshaller")

def ping_CRSDS(context, options):
    """ ping the CR/SDS service
    """
    while True:
        try:
            params = {}
            params['obj_url'] = options['obj_url']
            if options['create']:
                params['create'] = True

            encoded_params = urllib.urlencode(params)
            url = "%s?%s" % (options['service_to_ping'], encoded_params)
            logger.info("Pinging: %s for object: %s with create=%s" \
                % (options['service_to_ping'], 
                    options['obj_url'], 
                    options['create']))
            ping_con = urllib2.urlopen(url)
            ping_response = ping_con.read()
            # TODO check if error message is '<?xml version="1.0"?>\r\n<response>\r\n    <message>URL not in catalogue of sources, no action taken.</message>\r\n    <flerror>0</flerror>\r\n</response>'
            # if so, try to ping with create = true
            ping_con.close()
        except urllib2.HTTPError, err:
            logger.info(err.msg)

        break


def schedule_ping_CRSDS(context, create):
    """ generic event
    """
    # TODO check canonicals
    registry = queryUtility(IRegistry)
    if not registry:
        return

    settings = registry.forInterface(IRDFMarshallerSettings)
    if not settings:
        return
    if not settings.services_to_ping:
        return


    if IVersionEnhanced.providedBy(context):
        obj_versions = IGetVersions(context)

    else:
        obj_versions = [context]

    async = getUtility(IAsyncService)
    for service_to_ping in settings.services_to_ping:
        for obj in obj_versions:
            obj_url = obj.absolute_url()
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
