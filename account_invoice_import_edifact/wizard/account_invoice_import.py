# Copyright 2025 Trobz,
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import mimetypes
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from datetime import datetime
from lxml import etree
import logging
from collections import defaultdict
from odoo.tools import config

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _name = 'account.invoice.import'
    _inherit = ['account.invoice.import']

    def parse_invoice(self, invoice_file_b64, invoice_filename):
        assert invoice_file_b64, 'No invoice file'
        logger.info('Starting to import invoice %s', invoice_filename)
        file_data = base64.b64decode(invoice_file_b64)
        filetype = mimetypes.guess_type(invoice_filename)
        logger.debug('Invoice mimetype: %s', filetype)
        if filetype and filetype[0] in [("text/plain", None)]:
            parsed_inv = self.parse_edifact_invoice(file_data)
            if parsed_inv is False:
                raise UserError(_(
                    "This type of EDIFACT invoice is not supported. "
                    "Did you install the module to support this type "
                    "of file?"))
        else:
            return super().parse_invoice(invoice_file_b64, invoice_filename)

        # if 'attachments' not in parsed_inv:
        #     parsed_inv['attachments'] = {}
        # parsed_inv['attachments'][invoice_filename] = invoice_file_b64
        # # pre_process_parsed_inv() will be called again a second time,
        # # but it's OK
        # pp_parsed_inv = self.pre_process_parsed_inv(parsed_inv)
        # return pp_parsed_inv

    @api.model
    def parse_edifact_invoice(self, filecontent):
        edifact_model = self.env["base.edifact"]

        interchange = edifact_model._loads_edifact(filecontent)

        msg_type, __ = edifact_model._get_msg_type(interchange)

        supported = ["INVOIC"]
        if msg_type not in supported:
            raise UserError(
                _("{msg_type} document is not a Invoice document").format(
                    msg_type=msg_type
                )
            )

        bgm = interchange.get_segment("BGM")
        # Invoice number
        # BGM segment: ['380', 'BILL/2025/0001', '9']
        invoice_ref = bgm[1]

        rd = {
            "type": "in_invoice",
            "invoice_number": invoice_ref,
        }
        parties = self._prepare_edifact_parties(interchange)
        order_dict = {
            **rd,
            **self._prepare_edifact_dates(interchange),
            **self._prepare_edifact_currencies(interchange),
            **self._prepare_edifact_monetary_amounts(interchange),
            **parties,
        }

        lines = self._prepare_edifact_lines(interchange, order_dict)
        if lines:
            order_dict["lines"] = lines

        if order_dict["partner"]:
            order_dict["partner"] = self._get_partner_info(order_dict["partner"])
        if order_dict["company"]:
            order_dict["company"] = {
                "vat": self._get_partner(order_dict["company"]).vat,
            }
        return order_dict

    def _get_partner(self, id_number):
        bdio = self.env["business.document.import"]
        return bdio._match_partner(
                id_number,
                "",
                partner_type="customer",
            )

    def _get_partner_info(self, id_number):
        partner = self._get_partner(id_number)
        partner_info = {
            "vat": partner.vat,
            "name": partner.name,
            "email": partner.email,
            "website": partner.website,
            "phone": partner.phone,
            "zip": partner.zip,
            "state_code": partner.state_id.code if partner.state_id else False,
            "country_code": partner.country_id.code if partner.country_id else False,
            "ref": partner.ref,
        }
        return partner_info
    
    @api.model
    def _prepare_edifact_dates(self, interchange):
        dates = defaultdict(dict)
        edifact_model = self.env["base.edifact"]
        for seg in interchange.get_segments("DTM"):
            date_meaning_code = seg[0][0]
            if date_meaning_code == "137":
                dates["date"] = edifact_model.map2odoo_date(seg[0])
            if date_meaning_code == "13":
                dates["due_date"] = edifact_model.map2odoo_date(seg[0])
        return dates
    
    @api.model
    def _prepare_edifact_currencies(self, interchange):
        currencies = {}
        edifact_model = self.env["base.edifact"]
        for seg in interchange.get_segments("CUX"):
            usage_code = seg[0][0]
            if usage_code == "2":
                currencies["currency"] = edifact_model.map2odoo_currency(seg[0])
        return currencies
    
    @api.model
    def _prepare_edifact_monetary_amounts(self, interchange):
        monetary_amounts = {}
        for seg in interchange.get_segments("MOA"):
            usage_code = seg[0][0]
            if usage_code == "79":
                monetary_amounts["amount_untaxed"] = seg[0][1]
            elif usage_code == "86":
                monetary_amounts["amount_total"] = seg[0][1]
        return monetary_amounts

    @api.model
    def _prepare_edifact_parties(self, interchange):
        references = self._prepare_edifact_references(interchange)
        parties = self._prepare_edifact_name_and_address(interchange)
        if parties.get("partner"):
            parties["partner"]["edi_ctx"]["vendor_code"] = references.get("vendor_code")
        if references.get("invoice_ref"):
            parties["invoice_ref"] = references["invoice_ref"]
        if references.get("origin"):
            parties["origin"] = references["origin"]
        return parties
    
    @api.model
    def _prepare_edifact_references(self, interchange):
        """
        RFF segment: [['CR', 'IK142']]
        """
        refs = {}
        for seg in interchange.get_segments("RFF"):
            reference = seg[0]
            reference_code = reference[0]
            if reference_code == "ADE":
                # ['firstorder','backorder','advantage','nyp']
                refs["account_reference"] = reference[1]
            elif reference_code == "PD":
                # Promotion Deal Number
                # Number assigned by a vendor to a special promotion activity
                refs["promotion_number"] = reference[1]
            elif reference_code == "VA":
                # Unique number assigned by the relevant tax authority to identify a
                # party for use in relation to Value Added Tax (VAT).
                refs["vat"] = reference[1]
            elif reference_code == "IV":
                # Order reference number
                refs["invoice_ref"] = reference[1]
            elif reference_code == "ON":
                # Order reference number
                refs["origin"] = reference[1]

        return refs

    @api.model
    def _prepare_edifact_name_and_address(self, interchange):
        nads = {}
        edifact_model = self.env["base.edifact"]
        for seg in interchange.get_segments("NAD"):
            reference_code = seg[0]
            if reference_code == "BY":
                # NAD segment: ['BY', ['5450534001649', '', '9']]
                # Customer (Buyer's GLN)
                nads["company"] = edifact_model.map2odoo_partner(seg)
            elif reference_code == "SU":
                # Our number of Supplier's GLN
                # Can be used to check that we are not importing the order
                # in the wrong company by mistake
                nads["partner"] = edifact_model.map2odoo_partner(seg)
            elif reference_code == "DP":
                # Delivery Party
                nads["ship_to"] = edifact_model.map2odoo_address(seg)
            elif reference_code == "IV":
                # Invoice Party
                nads["invoice_to"] = edifact_model.map2odoo_address(seg)
        return nads
    
    @api.model
    def _prepare_edifact_lines(self, interchange, order_dict):
        edifact_model = self.env["base.edifact"]
        bdio = self.env["business.document.import"]
        order = order_dict["order"]
        partner_id_number = order_dict["company"]
        order_dict["unknown_products"] = []
        partner = bdio._match_partner(
            partner_id_number,
            "",
            partner_type="customer",
        )
        lines = []
        pia_list = []
        qty_list = []
        pri_list = []
        imd_list = []

        for i in interchange.get_segments("PIA"):
            if i[1][1] == "SA":
                pia_list.append(i)
        for i in interchange.get_segments("QTY"):
            if i[0][0] == "21" or i[0][0] == "12":
                qty_list.append(i)
        for i in interchange.get_segments("PRI"):
            pri_list.append(i)
        for i in interchange.get_segments("IMD"):
            if i[0] == "A" and i[1] == "":
                imd_list.append(i)

        for linseg in interchange.get_segments("LIN"):

            piaseg = pia_list.pop(0) if pia_list else None
            qtyseg = qty_list.pop(0) if qty_list else None
            priseg = pri_list.pop(0) if pri_list else None
            imdseg = imd_list.pop(0) if imd_list else None

            line = {
                "sequence": int(linseg[0]),
                "product": edifact_model.map2odoo_product(linseg, piaseg),
                "qty": edifact_model.map2odoo_qty(qtyseg),
            }

            price_unit = edifact_model.map2odoo_unit_price(priseg)
            # If the product price is not provided,
            # the price will be taken from the system
            if price_unit != 0.0:
                line["price_unit"] = price_unit

            description = edifact_model.map2odoo_description(imdseg)
            if description:
                line["name"] = description

            try:
                # Check product
                bdio._match_product(line["product"], "")
            except UserError as error:
                if (
                    order
                    and
                    partner.edifact_despatch_advice_ignore_lines_with_unknown_products
                ):
                    order.message_post(body=_(error.name))
                    order_dict["unknown_products"].append(line)
                    continue
                else:
                    raise error

            lines.append(line)

        return lines
