{
    'name': 'Campos Personalizados para from helpdesk_ticket',
    'version': '1.0',
    'summary': 'Añade campos personalizados a las tareas las intervenciones',
    'author': 'David',
    'depends': ['project', 'hr', 'sale_management', 'helpdesk_mgmt' ],
    'data': [
        'views/project_task_views.xml',
    ],
    'installable': True,
    'application': False,
}
