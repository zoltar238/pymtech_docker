from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string='ticket')
