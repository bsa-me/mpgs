# -*- coding: utf-8 -*-

{
    'name': 'Mastercard Payment Gateway Service (MPGS) Payment Acquirer (Enterprise)',
    'version': '1.0',
    'author': 'AL JAWAD SOFTWARE HOUSE',
    'category': 'Account',
    'description': """Mastercard Payment Gateway Service(MPGS) Payment Acquirer
    """,
    'website': 'https://www.al-jawad.ae',
    'summary': 'Mastercard Payment Gateway Service(MPGS) Payment Acquirer',
    'depends': ['base', 'website_sale'],
    'data': [
        'views/payment_mpgs_templates.xml',
        'views/payment_acquirer.xml',
        'data/payment_acquirer_data.xml',
    ],
    'external_dependencies': {
        'python': [
            'pycountry'
        ],
    },
    'images': ['static/description/master_card.jpg'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
