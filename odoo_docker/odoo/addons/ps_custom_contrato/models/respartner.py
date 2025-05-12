from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"
    contrato_count = fields.Integer(string="Contratos",
                                   compute='compute_contrato_count',
                                   default=0)
    def compute_contrato_count(self):
        for record in self:
            record.contrato_count = self.env['ps_custom_contrato.contrato'].search_count(
                [('cliente_id', '=', self.id)])
            
    def action_get_contratos_count(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contratos',
            'view_mode': 'list',
            'res_model': 'ps_custom_contrato.contrato',
            'domain': [('cliente_id', '=', self.id)],
            'context': "{'create': False}"
        }

