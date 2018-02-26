from eea.rdfmarshaller.interfaces import ILinkedData
from plone.app.layout.viewlets import ViewletBase
from Products.Marshall.registry import getComponent

try:
    from eea.cache import cache
except ImportError:
    from plone.memoize.ram import cache


def get_key(function, viewlet):

    return u"/".join(viewlet.context.getPhysicalPath())


class LinkedDataExportViewlet(ViewletBase):
    """ Export an object as linked data
    """

    @cache(get_key)
    def render(self):

        marshaller = getComponent('surfrdf')
        obj2surf = marshaller._add_content(self.context)

        if obj2surf is None:
            return ""

        tpl = u"""<script data-diazo-keep='true' type="application/ld+json">
%s
</script>"""

        data = ILinkedData(self.context).serialize(obj2surf)
        data = data.decode('utf-8')

        res = tpl % data

        return res
