# Copyright 2024 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import _, models, fields
from datetime import datetime
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    edifact_version = fields.Selection(
        [
            ("d96a", "D.96A"),
            ("d01b", "D.01B"),
        ],
        default="d96a",
        string="Edifact Version",
    )

    def edifact_purchase_generate_data(self):
        self.ensure_one()
        edifact_model = self.env["base.edifact"]
        lines = []
        interchange = self._edifact_purchase_get_interchange()

        header = self._edifact_purchase_get_header()
        product, vals = self._edifact_purchase_get_product()
        summary = self._edifact_purchase_get_summary(vals)
        lines += header + product + summary
        for segment in lines:
            interchange.add_segment(edifact_model.create_segment(*segment))
        return interchange.serialize()

    def _edifact_purchase_get_interchange(self):
        id_number = self.env["res.partner.id_number"]
        sender = id_number.search(
            [("partner_id", "=", self.user_id.partner_id.id)], limit=1
        )
        recipient = id_number.search([("partner_id", "=", self.partner_id.id)], limit=1)
        if not sender or not recipient:
            raise UserError(_("Partner is not allowed to use the feature."))
        sender_edifact = [sender.name, "14"]
        recipient_edifact = [recipient.name, "14"]
        syntax_identifier = ["UNOC", "3"]

        return self.env["base.edifact"].create_interchange(
            sender_edifact, recipient_edifact, self.id, syntax_identifier
        )

    def _edifact_purchase_get_address(self, partner):
        # We apply the same logic as:
        # https://github.com/OCA/edi/blob/
        # c41829a8d986c6751c07299807c808d15adbf4db/base_ubl/models/ubl.py#L39

        # oca/partner-contact/partner_address_street3 is installed
        if hasattr(partner, "street3"):
            return partner.street3 or partner.street2 or partner.street
        else:
            return partner.street2 or partner.street

    def _edifact_get_name_and_address(self, partner, code, id_number=""):
        street = self._edifact_purchase_get_address(partner)
        return [
            # partner information
            (
                "NAD",
                code,
                [id_number, "", "9"],
                "",
                partner.commercial_company_name,
                [street, ""],
                partner.city,
                partner.state_id.id,
                partner.zip,
                partner.country_id.code,
            ),
            # VAT registration number
            ("RFF", ["VA", partner.vat]),
        ]

    def _edifact_purchase_get_header(self):
        today = datetime.now().date().strftime("%Y%m%d")
        id_number = self.env["res.partner.id_number"]
        buyer_id_number = id_number.search(
            [("partner_id", "=", self.user_id.partner_id.id)]
        )
        seller_id_number = id_number.search([("partner_id", "=", self.partner_id.id)])

        header = [
            ("UNH", "1", ["ORDERS", "D", "96A", "UN", "EAN008"]),
            # Order
            ("BGM", ["220", "", "9", "ORDERS"], self.id, "9"),
            # 137: Document/message date/time
            ("DTM", ["137", today, "102"]),
            # 2: Delivery date/time, requested
            ("DTM", ["2", self.date_planned.strftime("%Y%m%d"), "102"]),
            ("PAI", ["", "", "42"]),
            # Mutually defined
            ("FTX", "ZZZ", "1", ["", "", "91"]),
            # Message batch number
            ("RFF", ["ALL", self.id]),
            # Reference date/time
            ("DTM", ["171", self.write_date.strftime("%Y%m%d"), "102"]),
            # Payment detail/remittance information
            ("FTX", "PMD", "", "", ""),
            # Terms of payments
            ("FTX", "AAB", "", "", "30 jours net"),
            # Delivery note number
            ("RFF", ["DQ", self.id]),
            # Purchasing contact
            ("CTA", "PD", [self.user_id.partner_id.id, ""]),
            # Telephone
            ("COM", [self.user_id.partner_id.phone or "", "TE"]),
            # Reference currency
            ("CUX", ["2", self.currency_id.name, "4"]),
            # Rate of exchange
            ("DTM", ["134", today, "102"]),
            # Main-carriage transport
            ("TDT", "20", "", "30", "31"),  # TODO: add detail of transport
            # Place of terms of delivery
            (
                "LOC",
                "1",
                "location identification",
            ),  # TODO: add location identification
        ]
        if self.edifact_version == "d01b":
            header[0] = ("UNH", "1", ["ORDERS", "D", "01B", "UN", "EAN010"])

        header = (
            header[:11]
            + self._edifact_get_name_and_address(
                self.user_id.partner_id, "BY", buyer_id_number.name
            )
            + self._edifact_get_name_and_address(
                self.partner_id, "SU", seller_id_number.name
            )
            + self._edifact_get_name_and_address(
                self.partner_id, "DP", seller_id_number.name
            )
            + header[11:]
        )

        return header

    def _edifact_purchase_get_product(self):
        number = 0
        segments = []
        vals = {}
        tax = {}
        for line in self.order_line:
            number += 1
            product_tax = 0
            product = line.product_id
            product_per_pack = line.product_uom._compute_quantity(
                line.product_qty, product.uom_id
            )
            if line.taxes_id and line.taxes_id.amount_type == "percent":
                product_tax = line.taxes_id.amount
                if product_tax not in tax:
                    tax[product_tax] = line.price_total
                else:
                    tax[product_tax] += line.price_total
            product_seg = [
                # Line item number
                ("LIN", number, "", [product.barcode or "", "EN"]),
                # Product identification of supplier's article number
                ("PIA", "1", [product.default_code, "SA", "", "91"]),
                # Item description of product
                (
                    "IMD",
                    "F",
                    ["", "", "", product.product_tmpl_id.description_sale],
                ),
                # Ordered quantity
                ("QTY", ["21", line.product_uom_qty, line.product_uom.name]),
                ("QTY", ["21", line.product_uom_qty, line.product_uom.name]),
                # Quantity per pack
                (
                    "QTY",
                    [
                        "52",
                        product_per_pack if product_per_pack else 1,
                        "PCE"
                    ]
                ),
                # # Received quantity
                # ("QTY", "48", line.qty_received, line.product_uom.name),
                # Line item amount
                ("MOA", "203", line.price_total),
                # Calculation net
                ("PRI", ["AAA", round(line.price_total / line.product_uom_qty, 2)]),
                ("PRI", ["AAB", round(line.price_total / line.product_uom_qty, 2)]),
                # Order number of line item
                ("RFF", ["PL", self.id]),
                # Reference date/time
                ("DTM", ["171", self.write_date.strftime("%Y%m%d"), "102"]),
                # Package
                ("PAC", line.product_uom_qty, ["", "51"], line.product_uom.name),
                # Package Identification
                ("PCI", "14"),
                # TODO: This place can add delivery to multiple locations
                # Tax information
                (
                    "TAX",
                    "7",
                    "VAT",
                    "",
                    "",
                    ["", "", "", product_tax],
                ),  # TODO: check value this again later
            ]
            segments.extend(product_seg)
        vals["tax"] = tax
        vals["total_line_item"] = number
        return segments, vals

    def _edifact_purchase_get_summary(self, vals):
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
            ("UNT", 33 + 11 * total_line_item + 2 * len(vals["tax"]), "1"),
        ]
        summary = summary[:-2] + tax_list + summary[-2:]
        return summary
