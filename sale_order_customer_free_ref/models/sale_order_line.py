# Copyright 2024 CamptoCamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    customer_exp_delivery_start = fields.Date(
        string="Customer Expected Delivery Start Date"
    )
    customer_exp_delivery_end = fields.Date(
        string="Customer Expected Delivery End Date"
    )
