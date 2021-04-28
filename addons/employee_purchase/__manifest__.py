# -*- coding: utf-8 -*-
{
    'name': "Employee Purchase",

    'summary': """
        Employee Request for product and Manager approves from portal""",

    'description': """
        Employee Purchase:
        This module serves employee and manager by providing a portal
        from where an employee can request for a product, the manager
        can approve/reject it.
    """,

    'author': "Siddhant Pageni",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/\
    # base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Portal',
    'version': '14.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'sale', 'purchase', 'portal',
                'purchase_stock', 'l10n_de', 'l10n_de_skr03'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/assets.xml',
        'data/employee_data.xml',
        'data/employee_purchase_email_data.xml',
        'views/employee_purchase_portal_templates.xml',
        'views/purchase_views.xml',
        'views/hr_employee_views.xml',
        'views/employee_purchase_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
