import surf
from eea.rdfmarshaller.interfaces import ISurfResourceModifier
from eea.rdfmarshaller.licenses.license import ILicenses, IPortalTypeLicenses
from plone import api
from Products.CMFCore.interfaces import IContentish
from zope.component import adapts
from zope.interface import implements


class ContentLicenseModifier(object):
    implements(ISurfResourceModifier)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """ Change the rdf resource
        """
        try:
            reg_types = api.portal.get_registry_record(
                'rdfmarshaller_type_licenses', interface=IPortalTypeLicenses
            )
        except KeyError:
            return None

        try:
            reg_licenses = api.portal.get_registry_record(
                'rdfmarshaller_licenses', interface=ILicenses)
        except KeyError:
            return None

        if not (reg_types and reg_licenses):
            return

        if self.context.portal_type not in reg_types.keys():
            return None  # No license assigned for this portal type

        license_id = reg_types[self.context.portal_type]
        licenses = [x for x in reg_licenses if x['id'] == license_id]

        if len(licenses) == 0:
            return None  # No license details for this license id

        License = resource.session.get_class(surf.ns.SCHEMA['URL'])
        RightsStatement = resource.session.get_class(
            surf.ns.DCTERMS['RightsStatement']
        )

        base_url = self.context.absolute_url()
        info = licenses[0]
        license_url = info.get("url", "")
        copyright = info.get("copyright", "")
        attribution = info.get("attribution", "")

        license = License(license_url)
        license.dcterms_title = info.get("id", "")
        license.save()
        resource.dcterms_license = license_url

        rights = RightsStatement(base_url + "#rights-statement")

        rights.rdfs_label = "Rights statement"
        rights.odrs_copyrightNotice = copyright
        rights.odrs_attributionText = attribution
        rights.odrs_attributionURL = base_url
        rights.odrs_contentLicense = license_url
        rights.odrs_dataLicense = license_url
        rights.save()

        resource.dcterms_rights = rights

        # text = json.dumps(
        #     {
        #         "@context": {
        #             "dcat": "http://www.w3.org/ns/dcat#",
        #             "dct": "http://purl.org/dc/terms/",
        #             "odrs": "http://schema.theodi.org/odrs#",
        #             "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        #         },
        #
        #         "@id": self.context.absolute_url(),
        #         "@type": type_,
        #         "dct:title": self.context.title,
        #
        #         "dct:license": {
        #             "@id": license_url,
        #             "dct:title": license_title
        #         },
        #
        #         "dct:rights": {
        #             "rdfs:label": "Rights Statement",
        #             "@id": self.context.absolute_url(),
        #             "odrs:copyrightNotice": copyright,
        #             "odrs:attributionText": attribution,
        #
        #             "odrs:attributionURL": {
        #                 "@id": self.context.absolute_url(),
        #             },
        #             "odrs:contentLicense": {
        #                 "@id": license_url
        #             },
        #             "odrs:dataLicense": {
        #                 "@id": license_url
        #             }
        #         }
        #     },
        #     indent=True
        # )
