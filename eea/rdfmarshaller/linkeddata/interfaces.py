from zope.interface import Interface
from zope.schema import Int, Text, TextLine


class ILinkedDataHomepageData(Interface):
    """ Store small bits of data for LinkedHomepage
    """

    name = TextLine(
        title=u"Organization website name",
        required=True
    )

    logo_url = TextLine(
        title=u"Logo url",
        description=u"Used to show logo of organization in search results. "
        u"See https://developers.google.com/search/docs/data-types/logo",
        required=True
    )

    search_action_url = TextLine(
        title=u"Search box action URL",
        default=u"/search?q={search_term_string}",
        description=u"Used to provide a search box when showing main page as "
        u"a result",
        required=False
    )

    logo_height = Int(title=u"Logo height, in pixels", default=190)
    logo_width = Int(title=u"Logo width, in pixels", default=190)

    social_profile_links = Text(
        title=u"Social profile links",
        description=u"""One link per line. Supported profile links are:
Facebook, Twitter, Google+, Instagram, YouTube, LinkedIn, Myspace, Pinterest,
SoundCloud, Tumblr""",
        required=False,
    )
