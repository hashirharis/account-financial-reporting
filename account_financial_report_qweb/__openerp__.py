# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'QWeb Financial Reports',
    'version': '9.0.0.1.0',
    'category': 'Reporting',
    'summary': """
        OCA Financial Reports
    """,
    'author': 'Camptocamp SA,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'account',
    ],
    'data': [
<<<<<<< 2ce8b69f6cdae37f067b275cc79e1894f142e110
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/ledger_report_wizard_view.xml',
        'wizard/open_invoice_wizard_view.xml',
        'report_menus.xml',
=======
        'menuitems.xml',
        'reports.xml',
        'wizard/general_ledger_wizard.xml',
        # 'wizard/partner_ledger_wizard.xml',
        'report/templates/ledger_general.xml',
>>>>>>> include work from Yannick on qweb ledger, rearrange
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
