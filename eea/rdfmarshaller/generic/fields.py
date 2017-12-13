import re

from plone.api.portal import get_tool

S_RE = re.compile(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s")


def shorten(text, sentences=1):
    """ Split plain text in sentences and returns required number of sentences

    Very simple method. Avoids dependency on nltk.

    Returns text (joined sentences)
    """

    # TODO: test for unicode
    sents = S_RE.split(text)

    return u' '.join(sents[:sentences]).strip()


class BaseShortenHTMLField2Surf(object):
    """ Base class for field adapters where a fallback value needs to be
    provided because the base value is too long
    """

    max_sentences = 1

    def __init__(self, field, context, session):
        self.field = field
        self.context = context
        self.session = session

    def get_raw_value(self):
        """ Should return the html value of a field

        For dexterity, use obj.fieldname.output
        For Archetypes, use obj.get<FieldName>()
        """
        raise NotImplementedError

    def alternate_value(self):
        # override this implementation with specifics
        html = self.get_raw_value()

        if html:
            portal_transforms = get_tool(name='portal_transforms')
            data = portal_transforms.convertTo('text/plain',
                                               html, mimetype='text/html')
            html = shorten(data.getData(), sentences=self.max_sentences)

        return html
