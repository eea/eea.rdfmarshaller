from collective.z3cform.datagridfield import BlockDataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from plone import api
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform import directives
from zope import schema
from zope.interface import Interface
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class ILicense(Interface):
    id = schema.ASCIILine(
        title=u"License Title",
        description=u"Used to assign a license to a portal type."
    )

    text = schema.Text(
        title=u"License Text",
        description=u"Human readable text of license"
    )

    copyright = schema.ASCIILine(
        title=u"Copyright Notice",
        description=u"Example: Crown copyright 2013"
    )

    attribution = schema.ASCIILine(
        title=u"Attribution Text",
        description=u"Example: Education Department"
    )

    url = schema.URI(
        title=u"License URL",
        description=u"Don't forget http:// or https://"
    )


class ILicenses(Interface):
    """ Define settings data structure for licenses """

    rdfmarshaller_licenses = schema.List(
        title=u"Licenses",
        description=u"Define available licenses",
        value_type=DictRow(title=u"License", schema=ILicense)
    )
    directives.widget(rdfmarshaller_licenses=BlockDataGridFieldFactory)


class LicensesEditForm(RegistryEditForm):
    """ Licenses definition edit form """

    schema = ILicenses
    label = u"Licenses definition"


class LicensesView(ControlPanelFormWrapper):
    """ Licenses edit form """

    form = LicensesEditForm


class IPortalTypeLicenses(Interface):
    """ Define settings data structure for portal types - licenses """

    rdfmarshaller_type_licenses = schema.Dict(
        title=u"Licenses",
        description=u"Choose licenses.",
        key_type=schema.Choice(
            title=u"Portal Type",
            vocabulary="plone.app.vocabularies.ReallyUserFriendlyTypes"),
        value_type=schema.Choice(
            title=u"License",
            vocabulary="eea.rdfmarshaller.licenses")
        )


class PortalTypeLicensesEditForm(RegistryEditForm):
    """ Portal Type Licenses edit form """
    schema = IPortalTypeLicenses
    label = u"Portal type licenses settings"


class PortalTypeLicensesView(ControlPanelFormWrapper):
    """ Portal types - licenses edit form """

    form = PortalTypeLicensesEditForm


@implementer(IVocabularyFactory)
class LicensesVocabulary(object):

    def __call__(self, context):
        try:
            licenses = api.portal.get_registry_record(
                'rdfmarshaller_licenses', interface=ILicenses)
            items = [
                SimpleTerm(str(y), str(y), str(y)) for y in [
                    x.get('id') for x in licenses]
                ]
        except Exception:
            items = [SimpleTerm(' ', ' ', ' ')]

        return SimpleVocabulary(items)


LicensesVocabularyFactory = LicensesVocabulary()
