# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    balance = fields.Float(string="Balance", compute="_compute_balance")

    def _compute_balance(self):
        if not self.env.context.get('from_date'):
            from_date = fields.Date.context_today(self)
        else:
            from_date = self.env.context['from_date']
        if not self.env.context.get('to_date'):
            to_date = fields.Date.context_today(self)
        else:
            to_date = self.env.context['to_date']
        if not self.env.context.get('target_move'):
            target_move = 'posted'
        else:
            target_move = self.env.context['target_move']
        if not self.env.context.get('company_id'):
            company_id = self.env.user.company_id.id
        else:
            company_id = self.env.context['company_id']
        for tax in self:
            tax.balance = tax.compute_balance(
                from_date, to_date, company_id, target_move)

    def compute_balance(
        self, from_date, to_date, company_id, target_move="posted"
    ):
        self.ensure_one()
        move_line_model = self.env['account.move.line']
        if target_move == 'posted':
            state = ['posted']
        elif target_move == 'all':
            state = ['posted', 'draft']
        else:
            state = []
        move_lines = move_line_model.search([
            ('tax_line_id', '=', self.id),
            ('date', '<=', to_date),
            ('date', '>=', from_date),
            ('move_id.state', 'in', state),
            ('company_id', '=', company_id),
        ])
        total = sum([l.balance for l in move_lines])
        return total