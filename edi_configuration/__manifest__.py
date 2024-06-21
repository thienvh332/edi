# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI Configuration",
    "summary": """
    Base module allowing configuration for EDI framework.
    """,
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "depends": ["base_edi", "edi_oca"],
    "data": [
        "data/edi_configuration.xml",
    ],
    "demo": [],
}
