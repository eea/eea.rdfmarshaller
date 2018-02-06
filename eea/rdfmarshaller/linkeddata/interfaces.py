from collective.z3cform.datagridfield.registry import DictRow

from zope.interface import Interface
from zope.schema import Choice, Int, List, Text, TextLine


class IContactPoint(Interface):
    telephone = TextLine(
        title=u"Telephone number",
        description=u"""An internationalized version of the phone number,
        starting with the "+" symbol and country code (+1 in the US and
        Canada).  Examples: "+1-800-555-1212", "+44-2078225951" """,
        required=False,
    )

    contactType = Choice(
        title=u"Contact Type",
        values=[
            "customer support", "technical support", "billing support",
            "bill payment", "sales", "reservations", "credit card support",
            "emergency", "baggage tracking", "roadside assistance",
            "package tracking"
        ],
        required=True,
    )

    availableLanguage = Text(
        title=u"Languages",
        description=u"""Languages may be specified by their common English
        name. If omitted, the language defaults to English. One per line""",
        required=False,
    )

    contactOption = Choice(
        title=u"Contact Option",
        description=u"Details about the phone number",
        values=["TollFree", "HearingImpairedSupported"],
        required=False
    )


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

    contact_points = List(
        title=u"Contact Points",
        description=u"Define available contact points",
        required=False,
        value_type=DictRow(title=u"Contact Point", schema=IContactPoint)
    )
