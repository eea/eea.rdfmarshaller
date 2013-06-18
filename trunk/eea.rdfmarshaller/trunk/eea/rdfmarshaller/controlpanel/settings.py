""" RDF Marshaller settings
"""
from plone.app.registry.browser import controlpanel
from eea.rdfmarshaller.controlpanel.interfaces import IRDFMarshallerSettings


class RDFMarshallerSettingsEditForm(controlpanel.RegistryEditForm):
    """ Edit form
    """
    schema = IRDFMarshallerSettings
    label = "RDF Marshaller Settings"


class RDFMarshallerSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    """ Control panel
    """
    form = RDFMarshallerSettingsEditForm
