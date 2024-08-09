# Copyright 2024 CamptoCamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    requested_delivery_period_start = fields.Date(
        string="Customer Expected Delivery Start Date"
    )
    requested_delivery_period_end = fields.Date(
        string="Customer Expected Delivery End Date"
    )
