# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import models


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    def _prepare_order(self, parsed_order, price_source):
        res = super()._prepare_order(parsed_order, price_source)
        res["requested_delivery_period_start"] = parsed_order.get(
            "requested_delivery_period_start"
        )
        res["requested_delivery_period_end"] = parsed_order.get(
            "requested_delivery_period_end"
        )
        return res

    def parse_ubl_sale_order(self, xml_root):
        res = super().parse_ubl_sale_order(xml_root)
        ns = xml_root.nsmap
        main_xmlns = ns.pop(None)
        ns["main"] = main_xmlns
        if "RequestForQuotation" in main_xmlns:
            root_name = "main:RequestForQuotation"
        elif "Order" in main_xmlns:
            root_name = "main:Order"
        requested_delivery_xpath = xml_root.xpath(
            "/%s/cac:Delivery/cac:RequestedDeliveryPeriod" % root_name, namespaces=ns
        )
        if requested_delivery_xpath:
            if requested_delivery_xpath[0].xpath("cbc:StartDate", namespaces=ns):
                res["requested_delivery_period_start"] = (
                    requested_delivery_xpath[0]
                    .xpath("cbc:StartDate", namespaces=ns)[0]
                    .text
                )
            if requested_delivery_xpath[0].xpath("cbc:EndDate", namespaces=ns):
                res["requested_delivery_period_end"] = (
                    requested_delivery_xpath[0]
                    .xpath("cbc:EndDate", namespaces=ns)[0]
                    .text
                )
        return res

    def parse_ubl_sale_order_line(self, line, ns):
        vals = super().parse_ubl_sale_order_line(line, ns)
        line_item = line.xpath("cac:LineItem", namespaces=ns)[0]
        expected_delivery_date = line_item.xpath(
            "cac:Delivery/cac:RequestedDeliveryPeriod", namespaces=ns
        )
        if expected_delivery_date:
            start_date = expected_delivery_date[0].xpath("cbc:StartDate", namespaces=ns)
            end_date = expected_delivery_date[0].xpath("cbc:EndDate", namespaces=ns)
            if start_date and end_date:
                vals["requested_delivery_period_start"] = start_date[0].text
                vals["requested_delivery_period_end"] = end_date[0].text
        return vals
