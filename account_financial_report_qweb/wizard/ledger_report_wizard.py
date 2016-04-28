# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api, _


class LedgerReportWizard(models.TransientModel):

    _name = "ledger.report.wizard"
    _description = "Ledger Report Wizard"

    company_id = fields.Many2one(comodel_name='res.company')
    date_range_id = fields.Many2one(comodel_name='date.range', required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    fy_start_date = fields.Date(default='2016-01-01')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='posted')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    amount_currency = fields.Boolean(string='With currency',
                                     default=False)
    centralize = fields.Boolean(string='Activate centralization',
                                default=False)
    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')
         ],
        string="Partner's",
        default='customer')
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )
    line_ids = fields.One2many(comodel_name='ledger.report.wizard.line',
                               inverse_name='wizard_id')

    def _query(self):
        query = """
              WITH view_q as (SELECT
                ml.date,
                acc.id AS account_id,
                ml.debit,
                ml.credit,
                ml.name as name,
                ml.ref,
                ml.journal_id,
                ml.partner_id,
                SUM(debit) OVER w_account - debit AS init_debit,
                SUM(credit) OVER w_account - credit AS init_credit,
                SUM(debit - credit) OVER w_account - (debit - credit)
                    AS init_balance,
                SUM(debit - credit) OVER w_account AS cumul_balance
              FROM
                account_account AS acc
                LEFT JOIN account_move_line AS ml ON (ml.account_id = acc.id)
                --INNER JOIN res_partner AS part ON (ml.partner_id = part.id)
              INNER JOIN account_move AS m ON (ml.move_id = m.id)
              WINDOW w_account AS (
                  PARTITION BY acc.code ORDER BY ml.date, ml.id)
              ORDER BY acc.id, ml.date)
              INSERT INTO ledger_report_wizard_line
              (
              date,
              name,
              journal_id,
              account_id,
              partner_id,
              ref,
              label,
              --counterpart
              debit,
              credit,
              cumul_balance,
              wizard_id
              )
              SELECT
              date,
              name,
              journal_id,
              account_id,
              partner_id,
              ref,
              ' TODO label ' as label,
              --counterpart
              debit,
              credit,
              cumul_balance,

              %(wizard_id)s as wizard_id
              from view_q where date >= %(fy_date)s
            """

        params = dict(fy_date=self.fy_start_date, wizard_id=self.id)
        self.env.cr.execute(query, params)
        return True

    @api.multi
    def button_view(self):
        return self.process()

    @api.multi
    def process(self):
        self._query()

        return {
            'domain': [('wizard_id', '=', self.id)],
            'name': _('Ledger lines'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'ledger.report.wizard.line',
            'view_id': False,
            'context': {'group_by': ['account_id', 'date:month']},
            'type': 'ir.actions.act_window'
        }

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end


class LedgerReportWizardLine(models.TransientModel):
    _name = 'ledger.report.wizard.line'

    wizard_id = fields.Many2one(comodel_name='ledger.report.wizard')

    name = fields.Char()
    label = fields.Char()
    ref = fields.Char()
    date = fields.Date()
    month = fields.Char()
    partner_name = fields.Char()
    partner_ref = fields.Char()
    account_id = fields.Many2one('account.account')
    account_code = fields.Char()
    journal_id = fields.Many2one('account.journal')
    partner_id = fields.Many2one('res.partner')

    init_credit = fields.Float()
    init_debit = fields.Float()
    debit = fields.Float()
    credit = fields.Float()
    balance = fields.Float()

    cumul_credit = fields.Float()
    cumul_debit = fields.Float()
    cumul_balance = fields.Float()

    init_credit = fields.Float()
    init_debit = fields.Float()
    init_balance = fields.Float()

    move_name = fields.Char()
    move_state = fields.Char()
    invoice_number = fields.Char()

    centralized = fields.Boolean()
