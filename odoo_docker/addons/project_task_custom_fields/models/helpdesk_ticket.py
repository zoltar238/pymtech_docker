from odoo import models, fields

class HelpdeskMgmt(models.Model):
    _inherit = 'helpdesk.ticket'

    fecha_aviso = fields.Datetime(string='Aviso')
    fecha_salida = fields.Datetime(string='Salida')
    sistema = fields.Text(string='Sistema')
    kilometros = fields.Integer(string='Kilómetros')
    solucion_provisional = fields.Text(string='Solución Provisional')
    solucion_definitiva = fields.Text(string='Solución Definitiva')
    actuacion = fields.Text(string='Actuación')

    # Agregamos explicitamente la tabla de relación Many2many
    materiales_ids = fields.Many2many(
        'product.product', 
        'helpdesk_ticket_product_rel',  # Nombre de la tabla de relación
        'helpdesk_ticket_id',  # Campo que referencia a helpdesk.ticket
        'product_id',  # Campo que referencia a product.product
        string='Productos'
    )

    observaciones = fields.Text(string='Observaciones')
    documentos = fields.Many2many('ir.attachment', string='Archivos')
    estado = fields.Selection([
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada')
    ], string='Estado', default='abierta')

    def action_crear_presupuesto(self):
        """
        Crea un presupuesto (sale.order) basado en el cliente del ticket.
        """
        self.ensure_one()  # Asegura que solo se procese un registro

        if not self.partner_id:
            raise UserError("Debe asignar un cliente antes de generar un presupuesto.")

        order_vals = {
            'partner_id': self.partner_id.id,  # Cliente del presupuesto
           
            'order_line': [(0, 0, {
                 (''')
                'product_id': product.id,
                'product_uom_qty': 1,  # Cantidad predeterminada
                'price_unit': product.lst_price,  # Precio del producto
                (''')
            }) for product in self.materiales_ids],  # Productos seleccionados
            
        }

        sale_order = self.env['sale.order'].create(order_vals)

        return {
            'name': 'Presupuesto',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }