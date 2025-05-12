# -*- coding: utf-8 -*-
from odoo import models, fields, api


class productos_addons(models.Model):
    _inherit = 'product.template'

    proveedor = fields.Many2one(
        'res.partner',
        string='Proveedor',
        ondelete='set null',
    )
    marca = fields.Char('Marca')
    modelo = fields.Char('Modelo')
    familia = fields.Char('Familia')
    subfamilia = fields.Char('Subfamilia')
    descuento1 = fields.Float('Descuento 1')
    descuento2 = fields.Float('Descuento 2')
    descuento3 = fields.Float('Descuento 3')
    estanteria = fields.Char('Estanteria')
    balda = fields.Char('Balda')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Definir multi_discount como campo computado
    multi_discount = fields.Char('Discounts', compute='_compute_multi_discount', store=True, readonly=False)

    @api.depends('product_id.product_tmpl_id.descuento1',
                 'product_id.product_tmpl_id.descuento2',
                 'product_id.product_tmpl_id.descuento3')
    def _compute_multi_discount(self):
        for record in self:
            if record.product_id and record.product_id.product_tmpl_id:
                tmpl = record.product_id.product_tmpl_id
                # Solo incluir valores mayores que 0
                descuentos = []
                if tmpl.descuento1 > 0:
                    descuentos.append(str(tmpl.descuento1 * 100))
                if tmpl.descuento2 > 0:
                    descuentos.append(str(tmpl.descuento2 * 100))
                if tmpl.descuento3 > 0:
                    descuentos.append(str(tmpl.descuento3 * 100))

                record.multi_discount = '+'.join(descuentos) if descuentos else ''
            else:
                record.multi_discount = ''
