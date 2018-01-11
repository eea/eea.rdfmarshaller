from collective.z3cform.datagridfield import BlockDataGridFieldFactory

from eea.rdfmarshaller.linkeddata import ILinkedDataHomepageData
from plone.z3cform import layout
from z3c.form import field, form


class EditLinkedDataHomepageForm(form.EditForm):
    fields = field.Fields(ILinkedDataHomepageData)
    fields['contact_points'].widgetFactory = BlockDataGridFieldFactory


EditLinkedDataHomepageView = layout.wrap_form(EditLinkedDataHomepageForm)
