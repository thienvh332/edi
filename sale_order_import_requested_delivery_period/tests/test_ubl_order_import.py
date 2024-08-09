# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

import base64

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
                "date_order": "2010-01-20",
                "partner": self.env.ref("sale_order_import_ubl.svensson"),
                "shipping_partner": self.env.ref(
                    "sale_order_import_ubl.swedish_trucking"
                ),
                "currency": self.env.ref("base.SEK"),
                "requested_delivery_period_start": "2010-02-10",
                "requested_delivery_period_end": "2010-02-25",
                "order_line": {
                    0: {
                        "requested_delivery_period_start": "2010-02-10",
                        "requested_delivery_period_end": "2010-02-25",
                    },
                    1: {
                        "requested_delivery_period_start": "2010-02-10",
                        "requested_delivery_period_end": "2010-02-25",
                    },
                },
            },
            "UBL-Order-2.0-Example.xml": {
                "date_order": "2010-06-20",
                "partner": self.env.ref("sale_order_import_ubl.fred_churchill"),
                "currency": self.env.ref("base.GBP"),
                "requested_delivery_period_start": "2005-06-29",
                "requested_delivery_period_end": "2005-06-29",
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
                self.assertEqual(so.date_order.strftime("%Y-%m-%d"), res["date_order"])
            if res.get("requested_delivery_period_start"):
                requested_delivery_period_start = (
                    so.requested_delivery_period_start.strftime("%Y-%m-%d")
                )
                self.assertEqual(
                    requested_delivery_period_start,
                    res["requested_delivery_period_start"],
                )
            if res.get("requested_delivery_period_end"):
                requested_delivery_period_end = (
                    so.requested_delivery_period_end.strftime("%Y-%m-%d")
                )
                self.assertEqual(
                    requested_delivery_period_end, res["requested_delivery_period_end"]
                )
            if res.get("order_line"):
                for key, val in res["order_line"].items():
                    if val.get("requested_delivery_period_start"):
                        requested_delivery_period_start = so.order_line[
                            key
                        ].requested_delivery_period_start.strftime("%Y-%m-%d")
                        self.assertEqual(
                            requested_delivery_period_start,
                            val["requested_delivery_period_start"],
                        )
                    if val.get("requested_delivery_period_end"):
                        requested_delivery_period_end = so.order_line[
                            key
                        ].requested_delivery_period_end.strftime("%Y-%m-%d")
                        self.assertEqual(
                            requested_delivery_period_end,
                            val["requested_delivery_period_end"],
                        )
