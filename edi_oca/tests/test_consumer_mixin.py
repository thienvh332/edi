# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# Copyright 2020 Camptocamp SA
# @author: Simone Orsi
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
from unittest import mock, skipIf

from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo.tests.common import Form, tagged

from .common import EDIBackendCommonTestCase


# This clashes w/ some setup (eg: run tests w/ pytest when edi_storage is installed)
# If you still want to run `edi` tests w/ pytest when this happens, set this env var.
@tagged("at_install", "-post_install")
@skipIf(os.getenv("SKIP_EDI_CONSUMER_CASE"), "Consumer test case disabled.")
class TestConsumerMixinCase(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import EdiExchangeConsumerTest

        cls.loader.update_registry((EdiExchangeConsumerTest,))
        cls.consumer_record = cls.env["edi.exchange.consumer.test"].create(
            {"name": "Test Consumer"}
        )
        cls.exchange_type_out.exchange_filename_pattern = "{record.id}"

        rule_vals = {
            "name": "Test",
            "model_id": cls.env["ir.model"]._get_id(cls.consumer_record._name),
            "kind": "custom",
            "enable_domain": "[]",
            "enable_snippet": """
result = not record._has_exchange_record(exchange_type)
""",
        }
        cls.exchange_type_new = cls._create_exchange_type(
            name="Test CSV output",
            code="test_csv_new_output",
            direction="output",
            exchange_file_ext="csv",
            backend_id=False,
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
            rule_ids=[(0, 0, rule_vals)],
        )
        rule_vals = {
            "name": "Test",
            "model_id": cls.env["ir.model"]._get_id(cls.consumer_record._name),
            "kind": "custom",
            "enable_domain": "[]",
            "enable_snippet": """
result = not record._has_exchange_record(exchange_type, exchange_type.backend_id)
""",
        }
        cls.exchange_type_out.write({"rule_ids": [(0, 0, rule_vals)]})
        cls.backend_02 = cls.backend.copy()

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_mixin(self):
        self.assertEqual(self.consumer_record.exchange_record_count, 0)
        vals = {
            "model": self.consumer_record._name,
            "res_id": self.consumer_record.id,
        }
        exchange_record = self.backend.create_record("test_csv_output", vals)
        self.assertEqual(self.consumer_record.exchange_record_count, 1)
        self.env["edi.exchange.record"].create(
            {
                "backend_id": self.backend.id,
                "type_id": self.exchange_type_new.id,
                "model": "an.other.model.with.same.id",
                "res_id": self.consumer_record.id,
            }
        )
        self.consumer_record.refresh()
        self.assertEqual(self.consumer_record.exchange_record_count, 1)
        action = self.consumer_record.action_view_edi_records()
        self.consumer_record.refresh()
        self.assertEqual(
            exchange_record, self.env["edi.exchange.record"].search(action["domain"])
        )
        self.assertTrue(
            self.consumer_record._has_exchange_record(
                exchange_record.type_id, self.backend
            )
        )

    def test_origin(self):
        vals = {
            "model": self.consumer_record._name,
            "res_id": self.consumer_record.id,
        }
        exchange_record = self.backend.create_record("test_csv_output", vals)
        self.consumer_record._edi_set_origin(exchange_record)
        self.assertEqual(
            self.consumer_record.origin_exchange_record_id, exchange_record
        )
        self.assertEqual(self.consumer_record._edi_get_origin(), exchange_record)

    def test_expected_configuration(self):
        # no btn enabled

        def make_config_data(**kw):
            data = {
                "form": {},
                "type": {
                    "id": self.exchange_type_out.id,
                    "name": self.exchange_type_out.name,
                },
            }
            data.update(kw)
            return data

        rule = self.exchange_type_out.rule_ids[0]
        self.assertFalse(self.consumer_record.edi_has_form_config)
        self.assertEqual(
            self.consumer_record.edi_config[str(rule.id)],
            make_config_data(),
        )
        # enable it
        self.exchange_type_out.rule_ids.kind = "form_btn"
        self.consumer_record.invalidate_cache(["edi_has_form_config", "edi_config"])
        self.assertEqual(
            self.consumer_record.edi_config[str(rule.id)],
            make_config_data(
                form={"btn": {"label": self.exchange_type_out.name, "tooltip": False}}
            ),
        )
        action = self.consumer_record.edi_create_exchange_record(
            self.exchange_type_out.id
        )
        self.assertEqual(action["res_model"], "edi.exchange.record")
        self.consumer_record.refresh()
        self.assertNotIn(
            str(rule.id),
            self.consumer_record.edi_config,
        )
        self.assertTrue(self.consumer_record.exchange_record_ids)
        self.assertEqual(
            self.consumer_record.exchange_record_ids.type_id, self.exchange_type_out
        )

    def test_multiple_backend(self):
        rule = self.exchange_type_new.rule_ids[0]
        self.assertIn(
            str(rule.id),
            self.consumer_record.edi_config,
        )
        action = self.consumer_record.edi_create_exchange_record(
            self.exchange_type_new.id
        )
        self.assertNotEqual(action["res_model"], "edi.exchange.record")
        self.assertEqual(action["res_model"], "edi.exchange.record.create.wiz")
        wizard = (
            self.env[action["res_model"]]
            .with_context(**action["context"])
            .create({"backend_id": self.backend_02.id})
        )
        wizard.create_edi()
        self.consumer_record.refresh()
        self.assertNotIn(
            str(rule.id),
            self.consumer_record.edi_config,
        )
        self.assertTrue(self.consumer_record.exchange_record_ids)
        self.assertEqual(
            self.consumer_record.exchange_record_ids.type_id, self.exchange_type_new
        )

    def test_form(self):
        """Testing that the form has inherited the fields and inserted them.

        Unfortunately we are unable to test the buttons here
        """
        with Form(self.consumer_record) as f:
            self.assertIn("edi_has_form_config", f._values)
            self.assertIn("edi_config", f._values)
            form = etree.fromstring(f._view["arch"])
            self.assertTrue(form.xpath("//field[@name='edi_has_form_config']"))
            self.assertTrue(form.xpath("//field[@name='edi_config']"))

    # Don't care about real data processing here
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._validate_data")
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._exchange_generate")
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._exchange_send")
    def test_edi_send_via_edi(self, mocked_send, mocked_generate, mocked_validate):
        mocked_generate.return_value = "result"
        self.assertEqual(self.consumer_record.exchange_record_count, 0)
        self.consumer_record._edi_send_via_edi(
            self.exchange_type_new, backend=self.backend
        )
        self.assertEqual(
            self.consumer_record.exchange_record_ids[0].type_id, self.exchange_type_new
        )
        self.assertEqual(
            self.consumer_record.exchange_record_ids[0]._get_file_content(), "result"
        )

    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._validate_data")
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._exchange_generate")
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._exchange_send")
    def test_edi_send_via_edi_ack(self, mocked_send, mocked_generate, mocked_validate):
        mocked_generate.return_value = "result"
        vals = {
            "model": self.consumer_record._name,
            "res_id": self.consumer_record.id,
        }
        origin_exchange_record = self.backend.create_record(
            self.exchange_type_in.code, vals
        )
        origin_exchange_record._set_file_content("original file")
        self.consumer_record._edi_set_origin(origin_exchange_record)
        self.assertEqual(self.consumer_record.exchange_record_count, 1)
        # Type out is an hack for the original record, they will be linked
        self.exchange_type_in.ack_type_id = self.exchange_type_out
        self.consumer_record._edi_send_via_edi(
            self.exchange_type_out, backend=self.backend
        )
        self.assertEqual(self.consumer_record.exchange_record_count, 2)
        ack_record = self.consumer_record.exchange_record_ids[1]
        self.assertEqual(ack_record.parent_id, origin_exchange_record)
        self.assertEqual(ack_record.type_id, self.exchange_type_out)
        self.assertEqual(ack_record._get_file_content(), "result")

    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._validate_data")
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._exchange_generate")
    @mock.patch("odoo.addons.edi_oca.models.edi_backend.EDIBackend._exchange_send")
    def test_edi_send_via_edi_invalid_ack(
        self, mocked_send, mocked_generate, mocked_validate
    ):
        mocked_generate.return_value = "result"
        vals = {
            "model": self.consumer_record._name,
            "res_id": self.consumer_record.id,
        }
        origin_exchange_record = self.backend.create_record(
            self.exchange_type_in.code, vals
        )
        origin_exchange_record._set_file_content("original file")
        self.consumer_record._edi_set_origin(origin_exchange_record)
        self.assertEqual(self.consumer_record.exchange_record_count, 1)
        # Type out is an hack for another type, they will not be linked
        self.exchange_type_in.ack_type_id = self.exchange_type_out_ack
        self.consumer_record._edi_send_via_edi(
            self.exchange_type_out, backend=self.backend
        )
        self.assertEqual(self.consumer_record.exchange_record_count, 2)
        ack_record = self.consumer_record.exchange_record_ids[1]
        self.assertFalse(ack_record.parent_id)
        self.assertEqual(ack_record.type_id, self.exchange_type_out)
        self.assertEqual(ack_record._get_file_content(), "result")
