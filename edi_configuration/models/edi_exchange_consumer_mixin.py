# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class EDIExchangeConsumerMixin(models.AbstractModel):

    _inherit = "edi.exchange.consumer.mixin"

    def edi_action_send(self, exchange_type):
        vals = {}
        vals.update(self._edi_create_exchange_record_vals(exchange_type))
        exc_record = exchange_type.backend_id.create_record(exchange_type.code, vals)
        return exc_record.action_exchange_generate_send()

    def edi_action_send_via_email(self, ir_action=None, partners=None):
        # add later
        pass
