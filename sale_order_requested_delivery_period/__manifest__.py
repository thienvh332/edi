# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Sale Order Requested Delivery Period",
    "version": "14.0.1.0.0",
    "category": "Sale",
    "license": "AGPL-3",
    "summary": """
        This module adds two new fields
        `requested_delivery_period_start` and `requested_delivery_period_end`
        to both the `sale.order` and `sale.order.line` models.
    """,
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["sale"],
    "data": ["views/sale_order.xml"],
    "installable": True,
}
