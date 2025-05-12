# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import math


class ProductPack(models.Model):
    _name = 'product.pack'
    _description = "Product Pack"

    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    qty_uom = fields.Float(string='Quantity', required=True, default=1.0)
    bi_product_template = fields.Many2one(comodel_name='product.template', string='Product pack')
    bi_image = fields.Image(related='product_id.image_1920', string='Image', store=True)
    price = fields.Float(related='product_id.lst_price', string='Product Price')
    uom_id = fields.Many2one(related='product_id.uom_id', string="Unit of Measure", readonly=True)
    name = fields.Char(related='product_id.name', readonly=True)


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_pack = fields.Boolean(string='Is Product Pack')
    cal_pack_price = fields.Boolean(string='Calculate Pack Price')
    pack_ids = fields.One2many(comodel_name='product.pack', inverse_name='bi_product_template', string='Product pack')

    @api.model_create_multi
    def create(self, vals_list):
        total = 0
        res = super(ProductProduct, self).create(vals_list)
        for rec, vals in zip(res, vals_list):
            if rec.cal_pack_price:
                if 'pack_ids' in vals or 'cal_pack_price' in vals:
                    for pack_product in res.pack_ids:
                        qty = pack_product.qty_uom
                        price = pack_product.product_id.list_price
                        total += qty * price
            if total > 0:
                rec.list_price = total
        return res

    def write(self, vals):
        total = 0
        res = super(ProductProduct, self).write(vals)
        for pk in self:
            if pk.cal_pack_price:
                if 'pack_ids' in vals or 'cal_pack_price' in vals:
                    for pack_product in pk.pack_ids:
                        qty = pack_product.qty_uom
                        price = pack_product.product_id.list_price
                        total += qty * price

        if total > 0:
            self.list_price = total
        return res

    def _compute_quantities_dict(self):
        # TDE FIXME: why not using directly the function fields ?
        variants_available = {
            p['id']: p for p in
            self.product_variant_ids.read(['qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty'])
        }
        prod_available = {}
        for template in self:
            qty_available = 0
            virtual_available = 0
            incoming_qty = 0
            outgoing_qty = 0
            if template.is_pack:
                qty_available = 0.0
                virtual_available = 0.0
                for pid in template.pack_ids.filtered(lambda x: x.product_id.is_storable):
                    if not pid.qty_uom == 0.0:
                        temp = math.floor(pid.product_id.qty_available / pid.qty_uom)
                        temp2 = math.floor(pid.product_id.virtual_available / pid.qty_uom)

                        if qty_available == 0.0:
                            qty_available = temp
                        elif qty_available < temp:
                            qty_available = qty_available
                        elif temp < qty_available:
                            qty_available = temp

                        if virtual_available == 0.0:
                            virtual_available = temp2
                        elif virtual_available < temp2:
                            virtual_available = virtual_available
                        elif temp2 < virtual_available:
                            virtual_available = temp2
                    else:
                        qty_available = 0.0
                        virtual_available = 0.0

                    incoming_qty += pid.product_id.incoming_qty
                    outgoing_qty += pid.product_id.outgoing_qty

                qty_available = qty_available
                virtual_available = virtual_available
                prod_available[template.id] = {
                    "qty_available": qty_available,
                    "virtual_available": virtual_available,
                    "incoming_qty": incoming_qty,
                    "outgoing_qty": outgoing_qty,
                }
                search_line = self.env['stock.quant'].search([('product_id.product_tmpl_id', '=', template.id)])
                if search_line:

                    for stock_line_id in search_line:
                        stock_line_id.write({'inventory_quantity': qty_available})
                        stock_line_id._compute_inventory_diff_quantity()
                        stock_line_id.action_apply_inventory()

            else:
                for p in template.product_variant_ids:
                    qty_available += variants_available[p.id]["qty_available"]
                    virtual_available += variants_available[p.id]["virtual_available"]
                    incoming_qty += variants_available[p.id]["incoming_qty"]
                    outgoing_qty += variants_available[p.id]["outgoing_qty"]
                prod_available[template.id] = {
                    "qty_available": qty_available,
                    "virtual_available": virtual_available,
                    "incoming_qty": incoming_qty,
                    "outgoing_qty": outgoing_qty,
                }
        return prod_available


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_bundle = fields.Boolean('Allow Manual Dropshipping Delivery')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        allow_bundle = self.env['ir.config_parameter'].sudo().get_param('product_bundle_pack.allow_bundle')
        res.update(
            allow_bundle=allow_bundle,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('product_bundle_pack.allow_bundle', self.allow_bundle)
