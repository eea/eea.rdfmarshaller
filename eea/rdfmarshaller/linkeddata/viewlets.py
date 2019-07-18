""" Viewlets Module
"""
import logging
from eea.rdfmarshaller.interfaces import ILinkedData
from plone.app.layout.viewlets import ViewletBase
from Products.Marshall.registry import getComponent
from zope.component import getMultiAdapter

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
    def render_viewlet(self):
        """ render viewlet """
        marshaller = getComponent('surfrdf')
        try:
            obj2surf = marshaller._add_content(self.context)
        except AssertionError, err:
            logger.exception(err)
            return ""

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

    def render(self):
        """ render """
        return self.render_viewlet() if self.available() else ""

    def available(self):
        """ Method that enables the viewlet only if we are on a
            view template
        """
        plone = getMultiAdapter((self.context, self.request),
                                name=u'plone_context_state')
        return plone.is_view_template()
