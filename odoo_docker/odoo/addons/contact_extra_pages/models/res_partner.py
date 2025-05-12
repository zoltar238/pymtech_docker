
from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # CCTV
    cctv_instal_existente = fields.Text('Instalación existente CCTV')
    cctv_camera = fields.Char("Cámara")
    cctv_camera_support = fields.Char("Soporte de cámara")
    cctv_power_supply = fields.Char("Fuente de alimentación cámara")
    cctv_recorder = fields.Char("Grabador")
    cctv_hd = fields.Char("HD")
    cctv_mouse = fields.Char("Ratón programador")
    cctv_remote = fields.Char("Mando")
    cctv_rack = fields.Char("Rack")

    # Portero
    intercom_instal_existente = fields.Text('Instalación existente Interfonía')
    intercom_model = fields.Char("Modelo")
    intercom_group = fields.Char("Grupo fónico")
    intercom_power = fields.Char("Alimentador")
    intercom_card_holder = fields.Char("Tarjetero")
    intercom_keyboard = fields.Char("Teclado")
    intercom_phones = fields.Char("Teléfonos")
    intercom_base = fields.Char("Base")
    intercom_relay = fields.Char("Relé")
    intercom_points = fields.Integer("I - Nº Puntos")
    intercom_maintenance_type = fields.Char("I - Tipo Mantenimiento")
    intercom_maintenance = fields.Boolean("I - Mantenimiento")

    # Antena colectiva
    antenna_instal_existente = fields.Text('Instalación existente Antena')
    antenna_capture_system = fields.Char("Sist Capta")
    antenna_amplification_system = fields.Char("Sist Amplif")
    antenna_box = fields.Char("Cofre")
    antenna_tdt = fields.Char("TDT")
    antenna_distribution_system = fields.Char("Sistema distribuido")
    antenna_sat = fields.Char("SAT")
    antenna_other_channels = fields.Char("Otros Canales")
    antenna_other_installations = fields.Char("Otras Instalaciones")
    antenna_maintenance = fields.Boolean("A - Mantenimiento")
    antenna_maintenance_type = fields.Char("A - Tipo Mantenimiento")
    antenna_points = fields.Integer("A - Nº Puntos")

    # Otras instalaciones
    otros_instal_existente = fields.Text('Instalaciones existentes')