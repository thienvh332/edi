# Copyright 2023 Camtocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def edifact_export_invoice(self):
        self.ensure_one()
        edifact_model = self.env["base.edifact"]
        lines = []
        interchange = self._edifact_export_invoice_interchange()

        header = self._edifact_export_invoice_header()
        product, vals = self._edifact_export_invoice_product()
        summary = self._edifact_export_invoice_summary(vals)
        lines += header + product + summary
        for segment in lines:
            interchange.add_segment(edifact_model.create_segment(*segment))
        return interchange.serialize()

    def _edifact_export_invoice_interchange(self):
        self.ensure_one()
        id_number = self.env["res.partner.id_number"]
        sender = id_number.search(
            [("partner_id", "=", self.invoice_user_id.partner_id.id)]
        )
        recipient = id_number.search([("partner_id", "=", self.partner_id.id)])
        if not sender or not recipient:
            raise UserError(_("Partner is not allowed to use the feature."))
        sender_edifact = [sender.name, "14"]
        recipient_edifact = [recipient.name, "14"]
        syntax_identifier = ["UNOC", "3"]

        return self.env["base.edifact"].create_interchange(
            sender_edifact, recipient_edifact, self.id, syntax_identifier
        )

    def _edifact_export_invoice_header(self):
        self.ensure_one()
        source_orders = self.line_ids.sale_line_ids.order_id
        today = datetime.now().date().strftime("%Y%m%d")
        id_number = self.env["res.partner.id_number"]
        buyer = self.partner_id

        seller = self.invoice_user_id.partner_id
        seller_id_number = id_number.search([("partner_id", "=", seller.id)])

        shipper = self.partner_shipping_id
        shipper_id_number = id_number.search([("partner_id", "=", shipper.id)])

        payment_term = min(self.invoice_payment_term_id.line_ids, default=None)
        discount_days = discount_percentage = 0
        if payment_term is not None:
            discount_days = payment_term.discount_days
            discount_percentage = payment_term.discount_percentage
        return [
            ("UNH", "1", ["INVOIC", "D", "96A", "UN", "EAN008"]),
            # Commercial invoice
            ("BGM", ["380", "", "", "Invoice"], self.payment_reference, "9"),
            # 35: Delivery date/time, actual
            (
                "DTM",
                [
                    "35",
                    max(
                        (
                            picking.date_done.date().strftime("%Y%m%d")
                            for order in source_orders
                            for picking in order.picking_ids
                            if picking.date_done
                        ),
                        default="",
                    ),
                    "102",
                ],
            ),  # TODO: Change datetime
            # 11: Despatch date and/or time
            (
                "DTM",
                [
                    "11",
                    min(
                        (
                            order.commitment_date.date().strftime("%Y%m%d")
                            for order in source_orders
                            if order.commitment_date
                        ),
                        default="",
                    ),
                    "102",
                ],
            ),
            # Document/message date/time
            ("DTM", ["137", today, "102"]),
            ("PAI", ["", "", "42"]),
            # Regulatory information
            ("FTX", "REG", "", "", ""),
            # Payment detail/remittance information
            ("FTX", "PMD", "", "", ""),
            # Terms of payments
            ("FTX", "AAB", "", "", "30 jours net"),
            # Delivery note number
            ("RFF", ["DQ", self.id]),
            # Reference date/time
            # TODO: fixed value for now, to be clarified
            ("DTM", ["171", "99991231", "102"]),
            # Invoice information
            (
                "NAD",
                "IV",
                [buyer.id, "", "92"],
                "",
                buyer.commercial_company_name,
                [buyer.street, ""],
                buyer.city,
                "",
                buyer.zip,
                buyer.country_id.code,
            ),
            # Internal customer number
            ("RFF", ["IT", buyer.id]),
            # Buyer information
            (
                "NAD",
                "BY",
                [buyer.id, "", "92"],
                "",
                buyer.commercial_company_name,
                [buyer.street, ""],
                buyer.city,
                "",
                buyer.zip,
                buyer.country_id.code,
            ),
            ("RFF", ["API", ""]),
            # Seller information
            (
                "NAD",
                "SE",
                [seller_id_number.name, "", "92"],
                "",
                seller.commercial_company_name,
                [seller.street, ""],
                seller.city,
                "",
                seller.zip,
                seller.country_id.code,
            ),
            # VAT registration number
            ("RFF", ["VA", seller.vat]),
            # Government reference number
            ("RFF", ["GN", seller.vat]),  # TODO: Fix it
            # Delivery party Information
            (
                "NAD",
                "DP",
                [shipper_id_number.name, "", "92"],
                "",
                shipper.commercial_company_name,
                [shipper.street, ""],
                shipper.city,
                "",
                shipper.zip,
                shipper.country_id.code,
            ),
            ("RFF", ["API", ""]),
            # Reference currency
            ("CUX", ["2", buyer.currency_id.name, "4"]),
            # Rate of exchange
            ("DTM", ["134", today, "102"]),
            ("PAT", "3"),
            # Terms net due date
            ("DTM", ["13", self.invoice_date_due, "102"]),
            # Discount terms
            (
                "PAT",
                "22",
                "",
                ["5", "3", "D", discount_days],
            ),  # TODO: check value this again later
            # Discount percentage
            (
                "PCD",
                "12",
                "0",
                discount_percentage,
            ),  # TODO: check value this again later
            # Penalty terms
            ("PAT", "20"),
            # Penalty percentage
            ("PCD", "15", "0"),  # TODO: check value this again later
            # Allowance percentage
            ("PCD", "1", "0", "13"),  # TODO: check value this again later
            # Allowance or charge amount
            ("MOA", "8", "0"),  # TODO: check value this again later
        ]

    def _edifact_export_invoice_product(self):
        self.ensure_one()
        number = 0
        segments = []
        vals = {}
        tax = {}
        for line in self.line_ids:
            if line.display_type == "product":
                order = line.sale_line_ids.order_id
                number += 1
                product_tax = 0
                product = line.product_id
                product_per_pack = line.product_uom_id._compute_quantity(
                    line.quantity, product.uom_id
                )
                if line.tax_ids and line.tax_ids.amount_type == "percent":
                    product_tax = line.tax_ids.amount
                    if product_tax not in tax:
                        tax[product_tax] = line.price_total
                    else:
                        tax[product_tax] += line.price_total
                product_seg = [
                    # Line item number
                    ("LIN", number, "", ["", "EN"]),
                    # Product identification of supplier's article number
                    ("PIA", "5", [product.id, "SA", "", "91"]),
                    # Item description of product
                    (
                        "IMD",
                        "ANM",
                        ["", "", "", product.product_tmpl_id.description_sale],
                    ),
                    # Invoiced quantity
                    ("QTY", "47", line.quantity, line.product_uom_id.name),
                    # Quantity per pack
                    (
                        "QTY",
                        "52",
                        product_per_pack if product_per_pack else 1,
                        "PCE",
                    ),  # TODO:check it again
                    # Pieces delivered
                    ("QTY", "46", line.sale_line_ids.qty_delivered),
                    # Line item amount
                    ("MOA", "203", line.price_total),
                    # Calculation net
                    ("PRI", ["AAA", line.price_total / line.quantity]),
                    ("PRI", ["AAB", line.price_total / line.quantity]),
                    # Order number of line item
                    ("RFF", ["ON", order.id]),
                    # Tax information
                    (
                        "PRI",
                        "7",
                        "VAT",
                        "",
                        "",
                        ["", "", "", product_tax],
                    ),  # TODO: check value this again later
                    # Allowance or charge amount of line item
                    ("MOA", ["8", "0"]),
                ]
                segments.extend(product_seg)
        vals["tax"] = tax
        vals["total_line_item"] = number
        return segments, vals

    def _edifact_export_invoice_summary(self, vals):
        self.ensure_one()
        tax_list = []
        total_line_item = vals["total_line_item"]
        if "tax" in vals:
            for product_tax, price_total in vals["tax"].items():
                # Tax Information
                tax_list.append(
                    ("TAX", "7", "VAT", "", price_total, ["", "", "", product_tax])
                )
                # Tax amount
                tax_list.append(("MOA", ["124", price_total * product_tax / 100]))
        summary = [
            ("UNS", "S"),
            # Number of line items in message
            ("CNT", ["2", total_line_item]),
            # Taxable amount
            ("MOA", ["125", self.amount_untaxed]),
            # Total amount
            ("MOA", ["128", self.amount_total]),
            # Tax amount
            ("MOA", ["124", self.amount_tax]),
            ("MOA", ["8", "0"]),
            ("UNT", 37 + 11 * total_line_item + 2 * len(vals["tax"]), "1"),
        ]
        summary = summary[:-2] + tax_list + summary[-2:]
        return summary
