# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _total_discount(self):
        for rec in self:
            discount_amount = 0
            for line in rec.order_line:
                discount_amount += line.discount_amount
            rec.discount_amount = discount_amount
            rec.avg_discount = (discount_amount*100)/rec.amount_untaxed if rec.amount_untaxed else 0

    discount_amount = fields.Float('Total Discount', compute="_total_discount", digits='Discount')
    avg_discount = fields.Float('Avg Discount', compute="_total_discount", digits='Discount')
    print_discount = fields.Boolean('Print Discount')
    print_discount_amount = fields.Boolean('Print Discount Amount')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _total_discount(self):
        for rec in self:
            discount = ((rec.discount*rec.price_unit)/100)
            rec.discount_per_unit = discount
            rec.discount_amount = discount*rec.product_qty
            rec.discounted_unit_price = rec.price_unit - discount

    discount_amount = fields.Float('Discount Amount', compute="_total_discount", digits='Discount')
    discount_per_unit = fields.Float('Discount Per Unit', compute="_total_discount", digits='Discount')
    multi_discount = fields.Char('Discounts')  # Este campo será sobreescrito por el otro módulo
    discounted_unit_price = fields.Float('Discounted Unit Price', compute="_total_discount", digits='Discount')

    @api.onchange('multi_discount')
    def _onchange_multi_discount(self):
        def apply_discount_chain(base, discounts):
            for d in discounts:
                d_clean = d.strip().replace('%', '')  # Elimina símbolo % si existe
                try:
                    percentage = float(d_clean)
                    base -= (percentage * base) / 100
                except ValueError:
                    continue  # Ignora valores inválidos
            return base

        for record in self:
            if record.multi_discount:
                try:
                    discounts = record.multi_discount.split("+")
                    base_amount = 100.0  # Para calcular el porcentaje total aplicado
                    final_amount = apply_discount_chain(base_amount, discounts)
                    record.discount = round(base_amount - final_amount, 2)
                except Exception:
                    record.discount = 0
            else:
                record.discount = 0
