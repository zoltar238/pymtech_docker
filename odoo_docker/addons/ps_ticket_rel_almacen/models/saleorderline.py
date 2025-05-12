from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    allowed_product_template_ids = fields.Many2many(
        comodel_name='product.template',
        compute='_compute_allowed_product_template_ids',
        store=False
    )

    @api.depends('order_id.allowed_product_template_ids')
    def _compute_allowed_product_template_ids(self):
        for line in self:
            line.allowed_product_template_ids = line.order_id.allowed_product_template_ids


class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    allowed_product_ids = fields.Many2many(
        comodel_name='product.product',
        compute='_compute_allowed_product_ids',
        store=False
    )

    @api.depends('order_id.allowed_product_ids')
    def _compute_allowed_product_ids(self):
        for line in self:
            line.allowed_product_ids = line.order_id.allowed_product_ids