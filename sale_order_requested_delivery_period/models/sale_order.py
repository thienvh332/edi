# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    requested_delivery_period_start = fields.Date(
        string="Customer Expected Delivery Start Date"
    )
    requested_delivery_period_end = fields.Date(
        string="Customer Expected Delivery End Date"
    )
