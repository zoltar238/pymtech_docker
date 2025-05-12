from odoo import models, fields

class Contrato(models.Model):
    _name = 'ps_custom_contrato.contrato'
    _description = 'Contrato de Servicio'

    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True)
    tipo_contrato = fields.Selection([
        ('m', 'Mantenimiento'),
        ('g', 'Garantía'),
    ], string='Tipo de Contrato', required=True)

    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', required=True)

    tipo_servicio = fields.Selection([
        ('antena', 'Antena'),
        ('interfonia', 'Interfonía'),
        ('cctv', 'CCTV'),
    ], string='Tipo de Servicio', required=True)
