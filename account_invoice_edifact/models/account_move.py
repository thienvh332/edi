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
        product = self._edifact_export_invoice_product()
        summary = self._edifact_export_invoice_summary()
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
        return [
            ("UNH", "1", ["INVOIC", "D", "96A", "UN", "EAN008"]),
            ("BGM", ["380", "", "", "Invoice"], self.payment_reference, "9"),
            ("DTM", ["35", "20230928", "102"]),  # TODO: Change datetime
            ("DTM", ["11", source_orders.commitment_date, "102"]),
            ("DTM", ["137", today, "102"]),
            ("PAI", ["", "", "42"]),
            ("FTX", "REG", "", "", ""),
            ("FTX", "PMD", "", "", ""),
            ("FTX", "AAB", "", "", "30 jours net"),
            ("RFF", ["DQ", self.id]),
            ("DTM", ["171", "99991231", "102"]),  # TODO: Change datetime
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
            ("RFF", ["IT", buyer.id]),
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
            ("RFF", ["VA", seller.vat]),
            ("RFF", ["GN", seller.vat]),
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
            ("CUX", ["2", buyer.currency_id.name, "4"]),
            ("DTM", ["134", today, "102"]),
            ("PAT", "3"),
            ("DTM", ["13", self.invoice_date_due, "102"]),
            (
                "PAT",
                "22",
                "",
                ["5", "3", "D", "0"],
            ),  # TODO: check value this again later
            ("PCD", "12", "0", "13"),  # TODO: check value this again later
            ("PAT", "20"),  # TODO: check value this again later
            ("PCD", "15", "0"),  # TODO: check value this again later
            ("PCD", "1", "0", "13"),  # TODO: check value this again later
            ("MOA", "8", "0"),  # TODO: check value this again later
        ]

    def _edifact_export_invoice_product(self):
        self.ensure_one()
        number = 0
        order = self.line_ids.sale_line_ids.order_id
        segments = []
        for line in self.line_ids:
            if line.display_type == "product":
                number += 1
                product = line.product_id
                product_seg = [
                    ("LIN", number, "", ["", "EN"]),
                    ("PIA", "5", [product.id, "SA", "", "91"]),
                    (
                        "IMD",
                        "ANM",
                        ["", "", "", product.product_tmpl_id.description_sale],
                    ),
                    ("QTY", "47", line.quantity, line.product_uom_id.name),
                    ("QTY", "52", "1", "PCE"),  # TODO: check value this again later
                    ("QTY", "46", line.sale_line_ids.qty_delivered),
                    ("MOA", "203", line.price_total),
                    ("PRI", ["AAA", line.price_total / line.quantity]),
                    ("PRI", ["AAB", line.price_total / line.quantity]),
                    ("RFF", ["ON", order.id]),
                    (
                        "PRI",
                        "7",
                        "VAT",
                        "",
                        "",
                        ["", "", "", "15"],
                    ),  # TODO: check value this again later
                    ("MOA", ["8", "0"]),
                    (
                        "TAX",
                        "7",
                        "VAT",
                        "",
                        "",
                        ["", "", "", "15"],
                    ),  # TODO: check value this again later
                ]
                segments.extend(product_seg)
        return segments

    def _edifact_export_invoice_summary(self):
        self.ensure_one()
        product_count = self.line_ids.search_count(
            [("move_id", "=", self.id), ("display_type", "=", "product")]
        )
        return [
            ("UNS", "S"),
            ("CNT", ["2", product_count]),
            ("MOA", ["125", self.amount_untaxed]),
            ("MOA", ["128", self.amount_total]),
            ("MOA", ["124", self.amount_tax]),
            (
                "TAX",
                "7",
                "VAT",
                "",
                "15.00",
                ["", "", "", "7.70"],
            ),  # TODO: check value this again later
            ("MOA", ["124", "1.16"]),  # TODO: check value this again later
            (
                "TAX",
                "7",
                "VAT",
                "",
                "310.56",
                ["", "", "", "2.50"],
            ),  # TODO: check value this again later
            ("MOA", ["124", "7.76"]),  # TODO: check value this again later
            ("MOA", ["8", "0"]),  # TODO: check value this again later
            ("UNT", "133", "1"),
        ]
