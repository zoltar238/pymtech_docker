# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, date


class purchase_wizard_product_bundle(models.TransientModel):
    _name = 'purchase.explore.bundle.bi'
    _description = 'purchase wizard product bundle'

    product_id = fields.Many2one('product.product', string='Bundle', required=True)
    product_qty = fields.Integer('   Quantity ', required=True, default=1)
    product_price = fields.Float(string="Unit Cost")
    pack_ids = fields.One2many('product.pack', related='product_id.pack_ids', string="Select Products")

    def button_explore_bundle_purchase(self):
        purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
        for pack in self.pack_ids:
            seller = pack.product_id._select_seller(
                partner_id=purchase_order.partner_id,
                quantity=pack.qty_uom * self.product_qty,
                date=date.today(),
                uom_id=pack.product_id.uom_id)
            if pack.product_id == pack.product_id and pack.uom_id == pack.product_id.uom_id:
                price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                             pack.product_id.supplier_taxes_id,
                                                                             pack.product_id.taxes_id) if seller else 0.0
                if price_unit and seller and purchase_order.currency_id and seller.currency_id != purchase_order.currency_id:
                    price_unit = seller.currency_id.compute(price_unit, purchase_order.currency_id)
                if self.product_id.is_pack:
                    product_lang = pack.product_id.with_context(
                        lang=purchase_order.partner_id.lang,
                        partner_id=purchase_order.partner_id.id,
                    )
                    test = self.env['purchase.order.line'].create({'order_id': self._context['active_id'],
                                                                   'product_id': pack.product_id.id,
                                                                   'name': pack.product_id.name,
                                                                   'date_planned': datetime.now(),
                                                                   'price_unit': price_unit,
                                                                   'product_uom': pack.product_id.uom_id.id,
                                                                   'product_qty': pack.qty_uom * self.product_qty
                                                                   })
                    test.name = product_lang.display_name
                    if product_lang.description_purchase:
                        test.name += '\n' + product_lang.description_purchase

    @api.onchange('product_id')
    def onchange_product_purchase(self):
        purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
        if self.product_id:
            self.product_price = self.product_id.standard_price
        else:
            pass

    @api.onchange('product_qty')
    def onchange_purchase_qty(self):
        self.onchange_product_purchase()
