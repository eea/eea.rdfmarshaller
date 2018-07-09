""" Viewlets Module
"""
import logging
from eea.rdfmarshaller.interfaces import ILinkedData
from plone.app.layout.viewlets import ViewletBase
from Products.Marshall.registry import getComponent

try:
    from eea.cache import cache
except ImportError:
    from plone.memoize.ram import cache


logger = logging.getLogger('eea.rdfmarshaller')

def get_key(function, viewlet):
    """ get_key """
    return u"/".join(viewlet.context.getPhysicalPath())


class LinkedDataExportViewlet(ViewletBase):
    """ Export an object as linked data
    """

    @cache(get_key)
    def render(self):
        """ render """
        marshaller = getComponent('surfrdf')
        obj2surf = marshaller._add_content(self.context)

        if obj2surf is None:
            return ""

        tpl = u"""<script data-diazo-keep='true' type="application/ld+json">
%s
</script>"""

        try:
            data = ILinkedData(self.context).serialize(obj2surf)
        except AssertionError, err:
            logger.exception(err)
            return ""

        data = data.decode('utf-8')
        res = tpl % data
        return res
