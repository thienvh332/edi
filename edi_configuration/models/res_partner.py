# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    edi_purchase_conf_ids = fields.One2Many(
        comodel_name="edi.configuration", string="EDI Purchase Config Ids"
    )
