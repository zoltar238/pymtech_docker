{
    'name': 'PS Contratos Personalizados',
    'version': '1.0',
    "author": "Pymtech Solutions",
    'category': 'Custom',
    'summary': 'Gestión de contratos de clientes',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/contrato_views.xml',
        'views/respartner.xml',
    ],
    'installable': True,
    'application': False,
    "license": "LGPL-3",
}