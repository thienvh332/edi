# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import DotDict, safe_eval


class EdiConfiguration(models.Model):
    _name = "edi.configuration"

    active = fields.Boolean(default=False)
    code = fields.Char(required=True, copy=False, index=True, unique=True)
    description = fields.Char(help="describe what the conf is for")
    backend_id = fields.Many2one(string="Backend", comodel_name="edi.backend")
    type_id = fields.Many2one(string="Exchange Type", comodel_name="edi.exchange.type")
    model = fields.Many2one(
        "ir.model", string="Model", help="model the conf applies to"
    )
    res_id = fields.Many2oneReference(
        string="Record Id",
        index=True,
        required=False,
        readonly=True,
        model_field="model",
        copy=False,
        help="",
    )
    record_id = fields.Reference(compute="_compute_record_id", store=True)
    trigger = fields.Selection(
        [
            ("none", "None"),
            ("on_post_account_move", "On Post Account Move"),
            ("on_so_confirm", "On Sales Order Confirm"),
        ],
        string="Trigger",
        default="none",
    )
    snippet_before_do = fields.Text(
        string="Snippet Before Do",
        help="Snippet to validate the state and collect records to do",
    )
    snippet_do = fields.Text(
        string="Snippet Do",
        help="""Used to do something specific here.
        Receives: operation, edi_action, vals, old_vals.""",
    )

    @api.depends("model_id", "res_id")
    def _compute_record_id(self):
        pass

    def _code_snippet_valued(self, snippet):
        snippet = snippet or ""
        return bool(
            [
                not line.startswith("#")
                for line in (snippet.splitlines())
                if line.strip("")
            ]
        )

    def _time_utils(self):
        return {
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "utc_now": self._utc_now,
            "date_to_string": self._date_to_string,
            "datetime_to_string": self._datetime_to_string,
            "time_to_string": lambda dt: dt.strftime("%H:%M:%S") if dt else "",
            "first_of": fields.first,
        }

    def _get_code_snippet_eval_context(self):
        """Prepare the context used when evaluating python code

        :returns: dict -- evaluation context given to safe_eval
        """
        ctx = {
            "uid": self.env.uid,
            "user": self.env.user,
            "DotDict": DotDict,
        }
        ctx.update(self._time_utils())
        return ctx

    def _evaluate_code_snippet(self, snippet, **render_values):
        if not self._code_snippet_valued(snippet):
            return {}
        eval_ctx = dict(render_values, **self._get_code_snippet_eval_context())
        if self.env.context.get("exec_snippet_before_do", False):
            safe_eval.safe_eval(snippet, eval_ctx, mode="exec", nocopy=True)
            result = eval_ctx.get("result", {})
            if not isinstance(result, dict):
                return {}
            return result
        return eval_ctx

    def edi_exec_snippet_before_do(self, **render_values):
        self.ensure_one()
        vals = self.with_context(exec_snippet_before_do=True)._evaluate_code_snippet(
            self.snippet_before_do, render_values
        )
        if vals["snippet_do_vars"]:
            # Add snippet_do_vars to list params of EDIAutoInfo
            pass
        return vals

    def edi_exec_snippet_do(self, record):
        self.ensure_one()
        # vals = {
        #     "operation": "do",
        #     "edi_action": self,
        #     "vals": record,
        #     "old_vals": record.copy(),
        # }
        # add later
        return

    @api.model
    def edi_get_conf(self, trigger, backend=None):
        domain = [("trigger", "=", trigger)]
        if backend:
            domain.append(("backend_id", "=", backend.id))
        else:
            domain.append(("backend_id", "=", self.type_id.backend_id.id))
        return self.search(domain)
