# -*- coding: utf-8 -*-
{
    'name': "PS Almacen con tickets y presupuestos",

    'summary': "Modulo para relacionar tickets y presupuestos con un solo almacen",

    'author': "Pymtech Solutions",

    'version': '0.1',

    'depends': ['base','helpdesk_mgmt','stock','sale_management'],

    'data': [
        'views/helpdeskticket.xml',
        'views/saleorder.xml',
        'views/searchbar.xml'
    ],
}

