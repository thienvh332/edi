# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, models


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def _hook_match_partner(self, partner_dict, chatter_msg, domain, order):
        """
        2 types
        partner_dict = {'gln':""}
        partner_dict = {'partner': {'gln':""}, 'address':{'country_code':"ES",...}}
        """
        partner = partner_dict.get("partner", partner_dict)
        partner_dict.get("address", False)
        if not partner.get("gln"):
            return super()._hook_match_partner(partner_dict, chatter_msg, domain, order)
        party_id = partner["gln"]

        partner_id_category = self.env.ref(
            "partner_identification_gln.partner_identification_gln_number_category"
        )
        if not partner_id_category:
            raise exceptions.UserError(
                _(
                    "partner_identification_gln module"
                    " should be installed with a xmlid: "
                    "partner_identification_gln_number_category"
                )
            )
        id_number = self.env["res.partner.id_number"].search(
            [("category_id", "=", int(partner_id_category)), ("name", "=", party_id)],
            limit=1,
        )
        if not id_number:
            ctx = partner.get(
                "edi_ctx", {"order_filename": _("Unknown"), "rff_va": _("Unknown")}
            )
            raise exceptions.UserError(
                _("Partner GLN Code: {party} not found in order file: '{file}' "
                    "from VAT registration number '{vat}'.").format(
                    party=party_id,
                    file=ctx.get("order_filename"),
                    vat=ctx.get("rff_va"),
                )
            )

        return id_number.partner_id
