# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api, _
from operator import itemgetter

# order to be placed on the report: field
FIELDS_TO_READ = {1: 'date',
                  0: 'account_id',
                  4: 'account_code',
                  2: 'move_name',
                  3: 'journal_id',
                  5: 'partner_name',
                  6: 'ref',
                  7: 'label',
                  8: 'debit',
                  9: 'credit',
                  30: 'amount_currency',
                  40: 'currency_code',
                  50: 'month',
                  60: 'partner_ref',
                  10: 'cumul_balance',
                  70: 'init_balance',
                  }


class LedgerReportWizard(models.TransientModel):

    _name = "ledger.report.wizard"
    _description = "Ledger Report Wizard"

    company_id = fields.Many2one(comodel_name='res.company')
    date_range_id = fields.Many2one(comodel_name='date.range', required=True)
    date_from = fields.Date()
    date_to = fields.Date()
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

    @api.multi
    def pre_print_report(self, data):
        data = {'form': {}}

        # will be used to attach the report on the main account
        vals = self.read(['amount_currency',
                          'account_ids',
                          'journal_ids',
                          'centralize',
                          'target_move',
                          'date_from',
                          'date_to',
                          'fiscalyear'])[0]
        data['form'].update(vals)
        return data

    @api.multi
    def _print_report(self, data):
        # we update form with display account value
        data = self.pre_print_report(data)
        Report = self.env['report'].with_context(landscape=True)
        return Report.get_action(
            self, 'account.report_generalledger_qweb',
            data=data)

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = ('journal_ids' in data['form'] and
                                 data['form']['journal_ids'] or False)
        result['state'] = ('target_move' in data['form'] and
                           data['form']['target_move'] or '')
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to',
                                  'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def check_report_xlsx(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        # data['model'] = 'general.ledger.line'
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to',
                                  'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=self.env.context.get('lang', 'en_US'))
        return self._print_report_xlsx(data)

    @api.multi
    def _print_report_xlsx(self, data):
        return {
            'name': 'export xlsx general ledger',
            'model': 'ledger.report.wizard',
            'type': 'ir.actions.report.xml',
            'report_name': 'ledger.report.wizard.xlsx',
            'report_type': 'xlsx',
            'context': self.env.context,
        }

    @api.multi
    def _get_centralized_move_ids(self, domain):
        """ Get last line of each selected centralized accounts """
        # inverse search on centralized boolean to finish the search to get the
        # ids of last lines of centralized accounts
        # XXX USE DISTINCT to speed up ?
        domain = domain[:]
        centralize_index = domain.index(('centralized', '=', False))
        domain[centralize_index] = ('centralized', '=', True)

        gl_lines = self.env['general.ledger.line'].search(domain)
        accounts = gl_lines.mapped('account_id')

        line_ids = []
        for acc in accounts:
            acc_lines = gl_lines.filtered(lambda rec: rec.account_id == acc)
            line_ids.append(acc_lines[-1].id)
        return line_ids

    @api.multi
    def _get_moves_from_dates_domain(self):
        """ Prepare domain for `_get_moves_from_dates` """
        domain = []
        if self.centralize:
            domain = [('centralized', '=', False)]
        start_date = self.date_from
        end_date = self.date_to
        if start_date:
            domain += [('date', '>=', start_date)]
        if end_date:
            domain += [('date', '<=', end_date)]

        if self.target_move == 'posted':
            domain += [('move_state', '=', 'posted')]

        if self.account_ids:
            domain += [('account_id', 'in', self.account_ids.ids)]

        return domain

    def compute_domain(self):
        ret = self._get_moves_from_dates_domain()
        if self.centralize:
            centralized_ids = self._get_centralized_move_ids(ret)
            if centralized_ids:
                ret.insert(0, '|')
                ret.append(('id', 'in', centralized_ids))
        return ret

    def initial_balance_line(self, amount, account_name, account_code, date):
        return {'date': date,
                'account_id': account_name,
                'account_code': account_code,
                'move_name': '',
                'journal_id': '',
                'partner_name': '',
                'ref': '',
                'label': _('Initial Balance'),
                'debit': '',
                'credit': '',
                'amount_currency': '',
                'currency_code': '',
                'month': '',
                'partner_ref': '',
                'cumul_balance': amount,
                'init_balance': ''}

    def group_general_ledger(self, report_lines, date_start):
        """
        group lines by account and order by account then date
        """
        result = {}
        accounts = report_lines.mapped('account_id')
        for account in accounts:
            lines = report_lines.filtered(
                lambda a: a.account_id.id == account.id)
            acc_full_name = account.name_get()[0][1]
            sorted_lines = sorted(lines.read(FIELDS_TO_READ.values()),
                                  key=itemgetter('date'))
            initial_balance = sorted_lines[0]['init_balance']
            sorted_lines.insert(0, self.initial_balance_line(initial_balance,
                                                             acc_full_name,
                                                             account.code,
                                                             date_start))
            result[acc_full_name] = sorted_lines

        return result

    def construct_header(self):
        result = {}

        result['title'] = _('General Ledger')
        filters = {}

        filters['centralized'] = _('%s' % self.centralize)
        filters['start_date'] = self.date_from
        filters['end_date'] = self.date_to

        filters['target_moves'] = self.target_move

        filters['accounts'] = _('All')
        if self.account_ids:
            filters['accounts'] = ', '.join([a.code for a in self.account_ids])

        result['filters'] = filters

        return result

    @api.multi
    def compute(self):
        self.ensure_one()
        # header filled with a dict
        header = []
        header.append(self.construct_header())
        # content filled with dicts
        content = []

        domain = self.compute_domain()
        report_lines = self.env['general.ledger.line'].search(domain)
        lines_general_ledger = self.group_general_ledger(report_lines,
                                                         self.date_from)
        content.append(lines_general_ledger)
        return {'header': header,
                'content': content}
