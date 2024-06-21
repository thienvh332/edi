# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class EDIBackend(models.Model):
    _inherit = "edi.backend"

    def exchange_generate_send(self, recordset, skip_send=False):
        for rec in recordset:
            job1 = rec.delayable().action_exchange_generate()
            if not skip_send:
                # Chain send job.
                # Raise prio to max to send the record out as fast as possible.
                job1.on_done(rec.delayable(priority=0).action_exchange_send())
            job1.delay()

    def _check_output_exchange_sync(
        self, skip_send=False, skip_sent=True, record_ids=None
    ):
        """Lookup for pending output records and take care of them.

        First work on records that need output generation.
        Then work on records waiting for a state update.

        :param skip_send: only generate missing output.
        :param skip_sent: ignore records that were already sent.
        """
        # Generate output files
        new_records = self.exchange_record_model.search(
            self._output_new_records_domain(record_ids=record_ids)
        )
        _logger.info(
            "EDI Exchange output sync: found %d new records to process.",
            len(new_records),
        )
        if new_records:
            self.exchange_generate_send(new_records, skip_send)

        if skip_send:
            return
        pending_records = self.exchange_record_model.search(
            self._output_pending_records_domain(
                skip_sent=skip_sent, record_ids=record_ids
            )
        )
        _logger.info(
            "EDI Exchange output sync: found %d pending records to process.",
            len(pending_records),
        )
        for rec in pending_records:
            if rec.edi_exchange_state == "output_pending":
                rec.with_delay().action_exchange_send()
            else:
                self._exchange_output_check_state(rec)
