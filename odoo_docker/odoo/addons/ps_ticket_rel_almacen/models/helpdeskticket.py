from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_warehouse = fields.Many2one(
        'stock.warehouse', 
        string="Almacén", 
        compute='_compute_x_warehouse',
        readonly=True,
        store=False,
        help="Este almacén se asigna automáticamente según el usuario asignado al ticket."
    )

    x_support_user1 = fields.Many2one(
        'res.users',
        string="Usuario Soporte 1"
    )
    x_support_user2 = fields.Many2one(
        'res.users',
        string="Usuario Soporte 2"
    )
    x_support_user3 = fields.Many2one(
        'res.users',
        string="Usuario Soporte 3"
    )

    def action_crear_presupuesto(self):
        self.ensure_one()

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'ticket_id': self.id,
            'warehouse_id': self.x_warehouse.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Presupuesto',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        if vals.get('user_id'):
            user = self.env['res.users'].browse(vals['user_id'])
            vals['x_warehouse'] = user.property_warehouse_id.id or False
        return super().create(vals)

    def write(self, vals):
        if 'user_id' in vals:
            user = self.env['res.users'].browse(vals['user_id'])
            vals['x_warehouse'] = user.property_warehouse_id.id or False
        return super().write(vals)

    @api.depends('user_id')
    def _compute_x_warehouse(self):
        for ticket in self:
            ticket.x_warehouse = ticket.user_id.property_warehouse_id