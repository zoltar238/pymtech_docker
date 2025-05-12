# -*- coding: utf-8 -*-
{
    'name': "PS Campos Personalizados de Productos",

    'summary': "Añade campos de Marca, Modelo, Familia, Subfamilia y Descuentos en productos",

    'description': """
        Este módulo extiende el modelo de productos para añadir los siguientes campos:
        - Marca
        - Modelo
        - Familia
        - Subfamilia
        - Descuentos
        
        Crea también las modificacioens necesarias en las vistas para mostrar los nuevos campos
    """,

    'author': "Pymtech Solutions",

    'category': 'Uncategorized',

    'version': '0.1',

    'depends': ['base','product','purchase'],

    'data': [
        'views/templateproducto.xml',
    ],
}