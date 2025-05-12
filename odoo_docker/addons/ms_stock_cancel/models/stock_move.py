from odoo import fields, models, api, http, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        for rec in self.filtered(lambda m: m.state == "done"):
            rec.move_line_ids._action_cancel_done()
            rec.write({"state": "cancel"})
        res = super(StockMove, self)._action_cancel()
        return res

    def action_draft(self):
        for rec in self.filtered(lambda m: m.state == "cancel"):
            rec.write({"state": "draft"})
