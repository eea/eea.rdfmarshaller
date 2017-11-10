from eea.rdfmarshaller.licenses.license import ILicenses
from eea.rdfmarshaller.licenses.license import IPortalTypeLicenses
from plone import api
from plone.app.layout.viewlets.common import ViewletBase
import json


class LicenseViewlet(ViewletBase):
    """ json-ld license content
    """

    @property
    def json_obj(self):
        """ Return assigned license for portal_type of this context or None

            Example:
            https://github.com/theodi/open-data-licensing/blob/master/
                    examples/simple-json-ld.json
        """

        try:
            reg_types = api.portal.get_registry_record(
                'rdfmarshaller_type_licenses', interface=IPortalTypeLicenses)
        except KeyError:
            reg_types = None

        try:
            reg_licenses = api.portal.get_registry_record(
                'rdfmarshaller_licenses', interface=ILicenses)
        except KeyError:
            reg_licenses = None

        text = None
        if reg_licenses is not None and reg_types is not None:
            if self.context.portal_type not in reg_types.keys():
                return None  # No license assigned for this portal type

            license_id = reg_types[self.context.portal_type]
            licenses = [
                x for x in reg_licenses if x['id'] == license_id]

            if len(licenses) == 0:
                return None  # No license details for this license id

            license = licenses[0]
            license_url = license.get("url", "")
            license_title = license.get("id", "")
            copyright = license.get("copyright", "")
            attribution = license.get("attribution", "")

            # [TODO] Update this.
            #
            # This is not using the eea.rdfmarshaller properly.
            # This is work that isn't yet commited, still in work by Tibi and
            # Alec, so it's fine for now, but will need refactoring.
            text = json.dumps(
                {
                    "@context": {
                        "dcat": "http://www.w3.org/ns/dcat#",
                        "dct": "http://purl.org/dc/terms/",
                        "odrs": "http://schema.theodi.org/odrs#",
                        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                    },

                    "@id": self.context.absolute_url(),
                    "@type": self.context.portal_type,
                    "dct:title": self.context.title,

                    "dct:license": {
                        "@id": license_url,
                        "dct:title": license_title
                    },

                    "dct:rights": {
                        "rdfs:label": "Rights Statement",
                        "@id": self.context.absolute_url(),
                        "odrs:copyrightNotice": copyright,
                        "odrs:attributionText": attribution,

                        "odrs:attributionURL": {
                            "@id": self.context.absolute_url(),
                        },
                        "odrs:contentLicense": {
                            "@id": license_url
                        },
                        "odrs:dataLicense": {
                            "@id": license_url
                        }
                    }
                }
            )

        return text

    def render(self):
        json_obj = self.json_obj
        if json_obj is None:
            return ""
        return """<script type="application/ld+json">{}</script>""".format(
                    json_obj
                )
