from odoo import fields, models, api, http, _
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_cancel_done(self):
        for rec in self.filtered(lambda ml: ml.state == "done"):
            quant_obj = self.env["stock.quant"]
            quant_obj._update_available_quantity(
                rec.product_id,
                rec.location_id,
                rec.quantity,
                lot_id=rec.lot_id,
                package_id=rec.package_id,
                owner_id=rec.owner_id,
            )
            quant_obj._update_available_quantity(
                rec.product_id,
                rec.location_dest_id,
                -rec.quantity,
                lot_id=rec.lot_id,
                package_id=rec.result_package_id,
                owner_id=rec.owner_id,
            )
