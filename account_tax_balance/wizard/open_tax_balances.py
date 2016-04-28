# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp.tools.translate import _


class OpenTaxBalances(models.TransientModel):
    _name = 'wizard.open.tax.balances'
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env.user.company_id)
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    date_range_id = fields.Many2one('date.range', 'Date range')
    move_state = fields.Selection(
        [('draft', 'Unposted'), ('posted', 'Posted')],
        string="Move state", required=True, default='posted'
    )

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.from_date = self.date_range_id.date_start
            self.to_date = self.date_range_id.date_end
        else:
            self.from_date = self.to_date = None

    @api.multi
    def open_taxes(self):
        self.ensure_one()
        view = self.env.ref('account_tax_balance.view_tax_tree_balance')
        action = {
            'name': _("Tax Balances"),
            'res_model': 'account.tax',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'context': {
                'from_date': self.from_date,
                'to_date': self.to_date,
                'move_state': self.move_state,
                'company_id': self.company_id.id,
            },
        }
        return action