from zope.interface import Interface
from zope.schema import TextLine


class ILinkedDataHomepageData(Interface):
    """ Store small bits of data for LinkedHomepage
    """

    name = TextLine(
        title=u"Organization website name",
        required=True
    )

    logo_url = TextLine(
        title=u"Logo url",
        description=u"Used to show logo of organization in search results",
        required=True
    )

    search_action_url = TextLine(
        title=u"Search box action URL",
        default=u"/search?q={search_term_string}",
        description=u"Used to provide a search box when showing main page as "
        u"a result",
        required=False
    )

    # logo_height = Attribute("Logo height")
    # logo_width = Attribute("Logo width")
