from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string='ticket')

    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Productos Permitidos",
        compute="_compute_allowed_product_ids",
        store=True,
    )

    allowed_product_template_ids = fields.Many2many(
        comodel_name="product.template",
        string="Plantillas de Productos Permitidos",
        compute="_compute_allowed_product_ids",
        store=True,
    )

    @api.depends('ticket_id', 'ticket_id.x_warehouse')
    def _compute_allowed_product_ids(self):
        for record in self:
            products = self.env['product.product']
            product_templates = self.env['product.template']
            
            if record.ticket_id and record.ticket_id.x_warehouse:
                warehouse = record.ticket_id.x_warehouse
                stock_quants = self.env['stock.quant'].search([
                    ('location_id.usage', '=', 'internal'),
                    ('location_id', 'child_of', warehouse.lot_stock_id.id),
                    ('quantity', '>', 0),
                ])
                products = stock_quants.mapped('product_id')  
                product_templates = products.mapped('product_tmpl_id')

            record.allowed_product_ids = products
            record.allowed_product_template_ids = product_templates  