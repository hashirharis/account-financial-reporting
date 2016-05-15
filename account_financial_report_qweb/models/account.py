# -*- coding: utf-8 -*-
# © 2011 Guewen Baconnier (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from openerp import api, fields, models
from openerp.tools import float_compare, float_is_zero


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_reconcile_domain(self, move, at_date):
        return [('create_date', '<=', at_date),
                '|', ('debit_move_id', '=', move.id),
                ('credit_move_id', '=', move.id)]

    @api.multi
    def _amount_residual_at_date(self):
        """ Computes the residual amount of a move line from a
        reconciliable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a
            non-reconciliable account, the original line amount
            for unreconciled lines,
            and something in-between for partially reconciled lines.
        """
        at_date = self.env.context.get('at_date', False)
        for line in self:
            if not at_date:
                line.amount_residual_on_date = line.amount_residual
                line.amount_residual_currency_at_date = \
                    line.amount_residual_currency
                continue
            if not line.account_id.reconcile:
                line.amount_residual_on_date = False
                continue
            #amounts in the partial reconcile table aren't signed,
            # so we need to use abs()
            amount = abs(line.debit - line.credit)
            amount_residual_currency = abs(line.amount_currency) or 0.0
            sign = 1 if (line.debit - line.credit) > 0 else -1
            if not line.debit and not line.credit \
                    and line.amount_currency and line.currency_id:
                #residual for exchange rate entries
                sign = 1 \
                    if float_compare(line.amount_currency, 0,
                                     precision_rounding=
                                     line.currency_id.rounding) == 1 else -1

            # Search for partial reconciliations
            partial_lines = self.env['account.partial.reconcile'].search(
            self._get_reconcile_domain(line, at_date))

            for partial_line in partial_lines:
                # If line is a credit (sign = -1) we:
                #  - subtract matched_debit_ids
                # (partial_line.credit_move_id == line)
                #  - add matched_credit_ids
                # (partial_line.credit_move_id != line)
                # If line is a debit (sign = 1), do the opposite.
                sign_partial_line = sign \
                    if partial_line.credit_move_id == line else (-1 * sign)

                amount += sign_partial_line * partial_line.amount
                #getting the date of the matched item to compute
                # the amount_residual in currency
                if line.currency_id:
                    if partial_line.currency_id \
                            and partial_line.currency_id == line.currency_id:
                        amount_residual_currency += \
                            sign_partial_line * partial_line.amount_currency
                    else:
                        if line.balance and line.amount_currency:
                            rate = line.amount_currency / line.balance
                        else:
                            date = partial_line.credit_move_id.date \
                                if partial_line.debit_move_id == line \
                                else partial_line.debit_move_id.date
                            rate = line.currency_id.with_context(
                                date=date).rate
                        amount_residual_currency += \
                            sign_partial_line * line.currency_id.round(
                                partial_line.amount * rate)

            # computing the `reconciled` field.
            # As we book exchange rate difference on each partial matching,
            # we can only check the amount in company currency
            reconciled = False
            digits_rounding_precision = line.company_id.currency_id.rounding
            if float_is_zero(amount,
                             precision_rounding=digits_rounding_precision):
                if line.currency_id and line.amount_currency:
                    if float_is_zero(
                            amount_residual_currency,
                            precision_rounding=line.currency_id.rounding):
                        reconciled = True
                else:
                    reconciled = True
            line.reconciled = reconciled

            line.amount_residual_at_date = \
                line.company_id.currency_id.round(amount * sign)
            line.amount_residual_currency_at_date = \
                line.currency_id and line.currency_id.round(
                    amount_residual_currency * sign) or 0.0

    amount_residual_at_date = fields.Monetary(
        compute='_amount_residual_at_date',
        string='Residual Amount at a certain at a date',
        currency_field='company_currency_id',
        help="The residual amount on a journal item expressed "
             "in the company currency, at a given date.")

    amount_residual_currency_at_date = fields.Monetary(
        compute='_amount_residual',
        string='Residual Amount in Currency at a date',
        help="The residual amount on a journal item expressed "
             "in its currency (possibly not the company currency), "
             "at a given date")
