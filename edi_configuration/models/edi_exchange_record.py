# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class EDIExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    def action_exchange_generate_send(self):
        return self.backend_id.exchange_generate_send(self)
