# Copyright 2025 Trobz,
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import EDIFACT',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import EDI EDIFACT supplier invoices/refunds',
    'author': 'Trobz,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': ['account_invoice_import', 'base_edifact', "partner_identification_gln"],
    'data': ['wizard/account_invoice_import_view.xml'],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
}
