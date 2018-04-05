from eea.rdfmarshaller.interfaces import ILinkedDataHomepage
from plone import api
from plone.autoform import directives
from plone.directives import form
from plone.formwidget.contenttree import PathSourceBinder
from plone.formwidget.contenttree.widget import MultiContentTreeWidget
from plone.z3cform import layout
from z3c.form import button, widget
from z3c.form.browser.checkbox import SingleCheckBoxFieldWidget as SCBFW
from z3c.form.interfaces import IFieldWidget
from zope import schema
from zope.interface import alsoProvides, implementer, noLongerProvides


@implementer(IFieldWidget)
def MultiContentTreeFieldWidget(field, request):
    default = []
    site_path = '/'.join(api.portal.get().getPhysicalPath())
    catalog = api.portal.get_tool('portal_catalog')

    brains = catalog.searchResults(
        object_provides=ILinkedDataHomepage.__identifier__)

    for brain in brains:
        if brain.getPath() is site_path:    # remove Plone site from path
            continue

        path = '/' + brain.getPath().split('/', 2)[2]
        default.append(path)

    field.default = default

    return widget.FieldWidget(field, MultiContentTreeWidget(request))


@implementer(IFieldWidget)
def SingleCheckBoxFieldWidget(field, request):
    """IFieldWidget factory for CheckBoxWidget."""
    widget = SCBFW(field, request)
    site = api.portal.get()
    already_set = ILinkedDataHomepage.providedBy(site)

    widget.field.default = already_set

    return widget


class IEditLinkedDataHomepages(form.Schema):
    set_plonesite = schema.Bool(
        title=u"Designate the Plone site as Homepage",
    )
    homepages = schema.List(
        title=u"Additional LinkedData Homepages inside this site",
        description=u"Select as many as you want",
        value_type=schema.Choice(
            title=u"Selection",
            source=PathSourceBinder(portal_type='Folder')
        )
    )

    directives.widget('homepages', MultiContentTreeFieldWidget)
    directives.widget('set_plonesite', SingleCheckBoxFieldWidget)


class EditLinkedDataHomepagesForm(form.SchemaForm):
    schema = IEditLinkedDataHomepages
    ignoreContext = True

    label = u"Set the LinkedData Homepages for this website"
    # description = u""

    def plone_homepage(self):
        """Returns the Plone site if it's marked with ILinkedDataHomepage"""
        site = api.portal.get()
        already_set = ILinkedDataHomepage.providedBy(site)

        if already_set:
            return site

    def homepages(self):
        """ Returns a list of brains that are marked with ILinkedDataHomepage
        """
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog.searchResults(
            object_provides=ILinkedDataHomepage.__identifier__)

        return brains

    @button.buttonAndHandler(u'Ok')
    def handleApply(self, action):
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage

            return

        site = api.portal.get()
        catalog = api.portal.get_tool('portal_catalog')
        already_set = ILinkedDataHomepage.providedBy(site)

        set_site = data['set_plonesite']

        if set_site != already_set:
            action = set_site and alsoProvides or noLongerProvides
            action(site, ILinkedDataHomepage)
            site._p_changed = True
            site.reindexObject(idxs=['object_provides'])

        brains = catalog.searchResults(
            object_provides=ILinkedDataHomepage.__identifier__)

        for brain in brains:
            # remove root and Plone site from path
            path = '/' + brain.getPath().split('/', 2)[2]

            if path not in data['homepages']:
                obj = brain.getObject()
                noLongerProvides(obj, ILinkedDataHomepage)
                obj.reindexObject(idxs=['object_provides'])

        for path in data['homepages']:
            path = path[1:]     # change to relative to Plone root path
            obj = site.restrictedTraverse(path)

            if not alsoProvides(obj, ILinkedDataHomepage):
                alsoProvides(obj, ILinkedDataHomepage)
                obj.reindexObject(idxs=['object_provides'])

        self.status = "Changes saved"

    @button.buttonAndHandler(u"Cancel")
    def handleCancel(self, action):
        """User cancelled. Redirect back to the front page.
        """


EditLinkedDataHomepagesView = layout.wrap_form(EditLinkedDataHomepagesForm)
