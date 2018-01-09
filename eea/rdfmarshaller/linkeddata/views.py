from eea.rdfmarshaller.linkeddata import ILinkedDataHomepageData
from plone.z3cform import layout
from z3c.form import field, form


class EditLinkedDataHomepageForm(form.EditForm):
    fields = field.Fields(ILinkedDataHomepageData)


EditLinkedDataHomepageView = layout.wrap_form(EditLinkedDataHomepageForm)
