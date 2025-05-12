from odoo import fields, models, api, http, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_draft(self):
        for rec in self.filtered(lambda p: p.state == 'cancel'):
            rec.move_ids.action_draft()
