# -*- coding: utf-8 -*-
# Author: Andrea andrea4ever Gallina
# Author: Francesco OpenCode Apruzzese
# Author: Ciro CiroBoxHub Urselli
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, api


class OpenInvoiceReport(models.AbstractModel):

    _name = 'report.account_financial_report_qweb.open_invoice_report_qweb'

    def _get_domain_moves(self, data):
        account_type = ('payable', 'receivable')
        if data['form']['result_selection'] == 'customer':
            account_type = ('receivable', )
        elif data['form']['result_selection'] == 'supplier':
            account_type = ('payable', )
        domain = [
            ('company_id', '=', data['form']['company_id'][0]),
            ('move_id.date', '<=', data['form']['at_date']),
            ('account_id.user_type_id.type', 'in', account_type),
            ('date_maturity', '!=', False)
            ]
        if data['form']['target_move'] != 'all':
            domain.append(('move_id.state', 'in', ('posted', )), )
        if data['form']['partner_ids']:
            domain.append(('partner_id', 'in',
                           [p.id for p in data['form']['partner_ids']]), )
        return domain

    def _get_domain_reconciliation(self, moves, data):
        domain = [
            ('create_date', '<=', data['form']['at_date']),
            '|', ('debit_move_id', 'in', moves.ids),
            ('credit_move_id', 'in', moves.ids)]
        return domain

    def _query(self, data):
        moves = self.env['account.move.line'].search(
            self._get_domain_moves(data), order='date asc')
        if not moves:
            return True  # ----- Show a message here
        recs = self.env['account.partial.reconcile'].search(
            self._get_domain_reconciliation(moves, data))
        rec_moves = {}
        for rec in recs:
            if rec.debit_move_id not in rec_moves:
                rec_moves[rec.debit_move_id] = rec.amount
            else:
                rec_moves[rec.debit_move_id] += rec.amount
            if rec.credit_move_id not in rec_moves:
                rec_moves[rec.credit_move_id] = - rec.amount
            else:
                rec_moves[rec.credit_move_id] -= rec.amount

        # We only want to fetch the unreconcile and partially reconciled moves.
        rec_moves_br = self.env['account.move.line'].browse()
        for move in moves:
            move_balance = move.debit - move.credit
            if move.id not in rec_moves.keys():
                rec_moves_br += move
            elif 0.0 < move_balance < rec_moves[move.id]:
                rec_moves_br += move
            elif rec_moves[move.id] < move_balance < 0.0:
                rec_moves_br += move
        return rec_moves_br

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        moves = self._query(data)
        docargs = {
            'doc_model': 'account.move.line',
            'doc_ids': data['ids'],
            'docs': moves.with_context(at_date=data['form']['at_date']),
            'header': data['header'],
            'account_obj': self.env['account.account'],
            'partner_obj': self.env['res.partner'],
            'currency_obj': self.env['res.currency'],
            }

        return report_obj.render(
            'account_financial_report_qweb.open_invoice_report_qweb',
            docargs)
