# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import SingleTransactionCase
from odoo.tools import file_open


class TestUblOrderImport(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_ubl_order_import(self):
        tests = {
            "UBL-Order-2.1-Example.xml": {
                "client_order_ref": "34",
                "date_order": "2010-01-20",
                "partner": self.env.ref("sale_order_import_ubl.svensson"),
                "shipping_partner": self.env.ref(
                    "sale_order_import_ubl.swedish_trucking"
                ),
                "invoicing_partner": self.env.ref("sale_order_import_ubl.karlsson"),
                "currency": self.env.ref("base.SEK"),
                "customer_exp_delivery_start": "2010-02-10",
                "customer_exp_delivery_end": "2010-02-25",
                "order_line": {
                    0: {
                        "customer_exp_delivery_start": "2010-02-10",
                        "customer_exp_delivery_end": "2010-02-25",
                    },
                    1: {
                        "customer_exp_delivery_start": "2010-02-10",
                        "customer_exp_delivery_end": "2010-02-25",
                    },
                },
            },
            "UBL-Order-2.0-Example.xml": {
                "client_order_ref": "AEG012345",
                "date_order": "2010-06-20",
                "partner": self.env.ref("sale_order_import_ubl.fred_churchill"),
                "shipping_partner": self.env.ref("sale_order_import_ubl.iyt"),
                "currency": self.env.ref("base.GBP"),
                "customer_exp_delivery_start": "2005-06-29",
                "customer_exp_delivery_end": "2005-06-29",
            },
        }
        for filename, res in tests.items():
            file_path = (
                "sale_order_import_ubl_customer_free_ref/tests/files/" + filename
            )
            with file_open(file_path, "rb") as f:
                xml_file = f.read()
            wiz = self.env["sale.order.import"].create(
                {"order_file": base64.b64encode(xml_file), "order_filename": filename}
            )
            f.close()
            action = wiz.import_order_button()
            so = self.env["sale.order"].browse(action["res_id"])
            self.assertEqual(so.partner_id, res["partner"])
            if res.get("currency"):
                self.assertEqual(so.currency_id, res["currency"])
            if res.get("client_order_ref"):

                self.assertEqual(so.customer_order_number, res["client_order_ref"])
                self.assertEqual(so.customer_order_free_ref, "MrBlue")
                self.assertEqual(
                    so.client_order_ref, res["client_order_ref"] + " - MrBlue"
                )

            if res.get("date_order"):
                date_order = fields.Datetime.to_string(so.date_order)
                self.assertEqual(date_order[:10], res["date_order"])
            if res.get("shipping_partner"):
                self.assertEqual(so.partner_shipping_id, res["shipping_partner"])
            if res.get("customer_exp_delivery_start"):
                customer_exp_delivery_start = so.customer_exp_delivery_start.strftime(
                    "%Y-%m-%d"
                )
                self.assertEqual(
                    customer_exp_delivery_start, res["customer_exp_delivery_start"]
                )
            if res.get("customer_exp_delivery_end"):
                customer_exp_delivery_end = so.customer_exp_delivery_end.strftime(
                    "%Y-%m-%d"
                )
                self.assertEqual(
                    customer_exp_delivery_end, res["customer_exp_delivery_end"]
                )
            if res.get("order_line"):
                for key, val in res["order_line"].items():
                    if val.get("customer_exp_delivery_start"):
                        customer_exp_delivery_start = so.order_line[
                            key
                        ].customer_exp_delivery_start.strftime("%Y-%m-%d")
                        self.assertEqual(
                            customer_exp_delivery_start,
                            val["customer_exp_delivery_start"],
                        )
                    if val.get("customer_exp_delivery_end"):
                        customer_exp_delivery_end = so.order_line[
                            key
                        ].customer_exp_delivery_end.strftime("%Y-%m-%d")
                        self.assertEqual(
                            customer_exp_delivery_end, val["customer_exp_delivery_end"]
                        )
