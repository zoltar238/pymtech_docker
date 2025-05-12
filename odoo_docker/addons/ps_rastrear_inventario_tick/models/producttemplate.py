from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        if 'is_storable' in fields:
            defaults['is_storable'] = True
        return defaults