import account
import tax_bracket
import income
import tax_deductions

from typing import List
from typing import Tuple
from typing import Dict

class YearlyTaxBracket(object):
    def __init__(self, bracket: tax_bracket.TaxBracket, amount_paid: float):
        self.bracket = bracket
        self.amount_paid = amount_paid

class YearlyTaxes:
    def __init__(self, cap_gains_taxes: float, income_taxes: float, income_brackets: List[YearlyTaxBracket]):
        self.cap_gains_taxes = cap_gains_taxes
        self.income_taxes = income_taxes
        self.income_brackets = income_brackets

    def total(self) -> float:
        return self.cap_gains_taxes + self.income_taxes

    @staticmethod
    def csv_header(income_tax_brackets: List[tax_bracket.TaxBracket]) -> str:
        output = ""
        for bracket in income_tax_brackets:
            output += f";{bracket.percentage};amount"
        return ";cap taxes;income taxes;total taxes" + output

    def csv(self) -> str:
        output = ""
        for yearly_bracket in self.income_brackets:
            output += f";${yearly_bracket.bracket.max_income:,.2f};${yearly_bracket.amount_paid:,.2f}"
        return f";${self.cap_gains_taxes:,.2f};${self.income_taxes:,.2f};${self.total():,.2f}{output}"


class YearlyWithdrawManager:

    def __init__(self,
                 post_tax_accounts: [account.Account],
                 pre_tax_accounts: [account.Account],
                 taxable_accounts: [account.Account],
                 pension_accounts: [income.Income],
                 income_tax_brackets: tax_bracket.TaxBracketCollection,
                 cap_gains_tax_brackets: tax_bracket.TaxBracketCollection,
                 standard_deductions: tax_deductions.StandardDeductions,
                 market_increase_by_year: Dict[int, float],
                 inflation_percent_by_year: Dict[int, float],
                 lump_sum_payments: [income.LumpSumPayment] = []):
        self.income_tax_brackets = income_tax_brackets
        self.cap_gains_tax_brackets = cap_gains_tax_brackets
        self.post_tax_accounts = post_tax_accounts
        self.pre_tax_accounts = pre_tax_accounts
        self.taxable_accounts = taxable_accounts
        self.pension_accounts = pension_accounts
        self.saving_accounts = taxable_accounts + post_tax_accounts + pre_tax_accounts
        self.taxes_per_year = {}
        self.standard_deductions = standard_deductions
        self.market_increase_by_year = market_increase_by_year
        self.inflation_percent_by_year = inflation_percent_by_year
        self._lump_sum_payments = lump_sum_payments

    def csv_header(self) -> str:
        output = ""
        for acc in self.saving_accounts:
            output += f"{acc.csv_header()}"

        for acc in self.pension_accounts:
            output += f"{acc.csv_header()}"

        for bracket in self.cap_gains_tax_brackets.brackets:
            output += f";{bracket.percentage}"

        output += ";standed"

        output += YearlyTaxes.csv_header(self.income_tax_brackets.brackets)

        output += ";market rate;inflation"

        return output

    def csv(self, year: int) -> str:
        output = ""
        for acc in self.saving_accounts:
            output += f"{acc.csv_values(year)}"

        for acc in self.pension_accounts:
            output += f"{acc.csv_values(year)}"

        for bracket in self.cap_gains_tax_brackets.brackets:
            output += f";${bracket.max_income:,.2f}"

        output += f";${self.standard_deductions.amount:,.2f}"
        output += self.taxes(year).csv()
        output += f";{self.market_increase_by_year[year]*100:,.1f}%"
        output += f";{self.inflation_percent_by_year[year]*100:,.1f}%"

        return output

    def __str__(self):
        output = ""

        if self.post_tax_accounts:
            output += "Post Tax Accounts \n"
            for acc in self.post_tax_accounts:
                output += f"{str(acc)}\n"
        if self.pre_tax_accounts:
            output += "Pre Tax Accounts \n"
            for acc in self.pre_tax_accounts:
                output += f"{str(acc)}\n"
        if self.taxable_accounts:
            output += "Taxable Accounts \n"
            for acc in self.taxable_accounts:
                output += f"{str(acc)}\n"

        return output

    def pay_taxes(self, amount: float, year: int):
        for acc in self.taxable_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.post_tax_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.pre_tax_accounts:
            amount = acc.withdraw(amount, year)

        return amount

    def set_total_predicted_income_taxes(self, year):
        amount = 0
        for pension in self.pension_accounts:
            amount += pension.predicted_yearly_taxable_income(year)

        for acc in self.post_tax_accounts:
            acc.total_taxable_pension_payments(amount, year)

    def conversions(self, year):
        # get total income tax
        # if income tax is not over total standard deduction
        # request conversions
        taxable_income = self._total_taxable_income(year)
        if taxable_income < self.standard_deductions.amount:
            amount_to_convert = self.standard_deductions.amount - taxable_income
            for acc in self.post_tax_accounts:
                amount_to_convert = acc.conversion(amount_to_convert, year)

            # add to roth
            self.pre_tax_accounts[0].add(self.standard_deductions.amount - taxable_income - amount_to_convert, year)
            # add to taxable
            # self.taxable_accounts[0].add(self.standard_deductions.amount - taxable_income - amount_to_convert, year)

    def payment(self, amount, year):
        self.taxable_accounts[0].add(amount, year)

    def lump_sum_payments(self, year):
        for payment in self._lump_sum_payments:
            if payment.year == year:
                self.taxable_accounts[0].add(payment.amount, year)

    def monthly_pension(self, year: int) -> float:
        amount = 0
        for pension in self.pension_accounts:
            amount += pension.payment(year)

        return amount

    def inflate(self, year: int):
        self.income_tax_brackets.inflate(year)
        self.cap_gains_tax_brackets.inflate(year)
        for pension in self.pension_accounts:
            pension.inflate(year)

        self.standard_deductions.inflate(year)

    def increase(self, year, month):
        for acc in self.saving_accounts:
            acc.increase(year, month)

        for pension in self.pension_accounts:
            pension.increase(year, month)

    def withdraw(self, amount: float, year: int) -> float:
        for acc in self.taxable_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.post_tax_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.pre_tax_accounts:
            amount = acc.withdraw(amount, year)

        return amount

    def taxes(self, year: int) -> YearlyTaxes:
        if year in self.taxes_per_year:
            return self.taxes_per_year[year]
        else:
            taxable_income = self._total_taxable_income(year)
            cap_gains = self._total_cap_gains(year)
            income_taxes, income_brackets = self._calc_income_taxes(taxable_income)
            cap_gains_taxes = self._calc_cap_gains_taxes(taxable_income, cap_gains)
            yearly_taxes = YearlyTaxes(cap_gains_taxes, income_taxes, income_brackets)
            self.taxes_per_year[year] = yearly_taxes

            return yearly_taxes

    def _calc_cap_gains_taxes(self, taxable_income: float, total_cap_gains: float) -> float:
        if taxable_income > self.cap_gains_tax_brackets.brackets[0].max_income:
            return total_cap_gains * self.cap_gains_tax_brackets.brackets[1].percentage
        else:
            cap_under_first_bracket = \
                min(self.cap_gains_tax_brackets.brackets[0].max_income - taxable_income, total_cap_gains)
            cap_over_first_bracket = total_cap_gains - cap_under_first_bracket
            return cap_over_first_bracket * self.cap_gains_tax_brackets.brackets[1].percentage

    def _calc_income_taxes(self, taxable_income: float) -> Tuple[float, List[YearlyTaxBracket]]:
        taxes = 0.0
        previous_max = 0.0
        taxable_income_after_deductions = taxable_income - self.standard_deductions.amount
        if taxable_income_after_deductions < 0.0:
            yearly_brackets = [YearlyTaxBracket(bracket, 0) for bracket in self.income_tax_brackets.brackets]
            return 0.0, yearly_brackets

        yearly_brackets = []
        for bracket in self.income_tax_brackets.brackets:
            if taxable_income_after_deductions > bracket.max_income:
                taxes += (bracket.max_income - previous_max) * bracket.percentage
                previous_max = bracket.max_income
                yearly_brackets.append(YearlyTaxBracket(bracket, bracket.max_income))
            else:
                amount_bracket = taxable_income_after_deductions - previous_max
                if amount_bracket > 0:
                    taxes += amount_bracket * bracket.percentage
                    yearly_brackets.append(YearlyTaxBracket(bracket, amount_bracket))
                else:
                    yearly_brackets.append(YearlyTaxBracket(bracket, 0))
                previous_max = bracket.max_income

        return taxes, yearly_brackets

    def _total_taxable_income(self, year: int) -> float:
        amount = 0.0
        for acc in self.taxable_accounts:
            amount += acc.taxable_income(year)

        for acc in self.post_tax_accounts:
            amount += acc.taxable_income(year)

        for acc in self.pre_tax_accounts:
            amount += acc.taxable_income(year)

        for acc in self.pension_accounts:
            amount += acc.taxable_income(year)

        return amount

    def _total_cap_gains(self, year: int) -> float:
        amount = 0.0
        for acc in self.saving_accounts:
            amount += acc.cap_taxable_income(year)

        return amount

class BucketWithdrawManager:

    def __init__(self,
                 post_tax_accounts: [account.Account],
                 pre_tax_accounts: [account.Account],
                 taxable_accounts: [account.Account],
                 pension_accounts: [income.Income],
                 income_tax_brackets: tax_bracket.TaxBracketCollection,
                 cap_gains_tax_brackets: tax_bracket.TaxBracketCollection,
                 standard_deductions: tax_deductions.StandardDeductions,
                 market_increase_by_year: Dict[int, float],
                 inflation_percent_by_year: Dict[int, float],
                 five_year_note_rate_by_year: Dict[int, float],
                 lump_sum_payments: [income.LumpSumPayment] = [],
                 bonds: [] = []):
        self.income_tax_brackets = income_tax_brackets
        self.cap_gains_tax_brackets = cap_gains_tax_brackets
        self.post_tax_accounts = post_tax_accounts
        self.pre_tax_accounts = pre_tax_accounts
        self.taxable_accounts = taxable_accounts
        self.pension_accounts = pension_accounts
        self.bonds = bonds
        self.saving_accounts = bonds + taxable_accounts + post_tax_accounts + pre_tax_accounts
        self.taxes_per_year = {}
        self.standard_deductions = standard_deductions
        self.market_increase_by_year = market_increase_by_year
        self.inflation_percent_by_year = inflation_percent_by_year
        self._lump_sum_payments = lump_sum_payments
        self.five_year_note_rate_by_year = five_year_note_rate_by_year
        self.running_index = 1.0
        self.index_highest = 1.0

    def networth(self):
        amount = 0.0
        for acc in self.saving_accounts:
            amount += acc.total_amount()

        return amount

    def csv_header(self) -> str:
        output = ";networth"
        for acc in self.saving_accounts:
            output += f"{acc.csv_header()}"

        for acc in self.pension_accounts:
            output += f"{acc.csv_header()}"

        for bracket in self.cap_gains_tax_brackets.brackets:
            output += f";{bracket.percentage}"

        output += ";standed"

        output += YearlyTaxes.csv_header(self.income_tax_brackets.brackets)

        output += ";market rate;inflation"

        return output

    def csv(self, year: int) -> str:
        output = f";${self.networth()}"
        for acc in self.saving_accounts:
            output += f"{acc.csv_values(year)}"

        for acc in self.pension_accounts:
            output += f"{acc.csv_values(year)}"

        for bracket in self.cap_gains_tax_brackets.brackets:
            output += f";${bracket.max_income:,.2f}"

        output += f";${self.standard_deductions.amount:,.2f}"
        output += self.taxes(year).csv()
        output += f";{self.market_increase_by_year[year]*100:,.1f}%"
        output += f";{self.inflation_percent_by_year[year]*100:,.1f}%"

        return output

    def __str__(self):
        output = ""

        if self.post_tax_accounts:
            output += "Post Tax Accounts \n"
            for acc in self.post_tax_accounts:
                output += f"{str(acc)}\n"
        if self.pre_tax_accounts:
            output += "Pre Tax Accounts \n"
            for acc in self.pre_tax_accounts:
                output += f"{str(acc)}\n"
        if self.taxable_accounts:
            output += "Taxable Accounts \n"
            for acc in self.taxable_accounts:
                output += f"{str(acc)}\n"

        return output

    def pay_taxes(self, amount: float, year: int):
        for acc in self.taxable_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.post_tax_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.pre_tax_accounts:
            amount = acc.withdraw(amount, year)

        return amount

    def set_total_predicted_income_taxes(self, year):
        amount = 0
        for pension in self.pension_accounts:
            amount += pension.predicted_yearly_taxable_income(year)

        for acc in self.post_tax_accounts:
            acc.total_taxable_pension_payments(amount, year)

    def conversions(self, year):
        # get total income tax
        # if income tax is not over total standard deduction
        # request conversions
        taxable_income = self._total_taxable_income(year)
        if taxable_income < self.standard_deductions.amount:
            amount_to_convert = self.standard_deductions.amount - taxable_income
            for acc in self.post_tax_accounts:
                amount_to_convert = acc.conversion(amount_to_convert, year)

            # add to roth
            self.pre_tax_accounts[0].add(self.standard_deductions.amount - taxable_income - amount_to_convert, year)
            # add to taxable
            # self.taxable_accounts[0].add(self.standard_deductions.amount - taxable_income - amount_to_convert, year)

    def payment(self, amount, year):
        self.taxable_accounts[0].add(amount, year)

    def lump_sum_payments(self, year):
        for payment in self._lump_sum_payments:
            if payment.year == year:
                self.taxable_accounts[0].add(payment.amount, year)

        for bond in self.bonds:
            amount = bond.lump_sum_payments(year)
            if amount > 0:
                self.taxable_accounts[0].add(amount, year)

    def monthly_pension(self, year: int) -> float:
        amount = 0
        for pension in self.pension_accounts:
            amount += pension.payment(year)

        for bond in self.bonds:
            amount += bond.monthly_payment(year)

        return amount

    def inflate(self, year: int):
        self.income_tax_brackets.inflate(year)
        self.cap_gains_tax_brackets.inflate(year)
        for pension in self.pension_accounts:
            pension.inflate(year)

        self.standard_deductions.inflate(year)
        self.running_index = self.running_index * (1 + self.market_increase_by_year[year])
        if self.running_index > self.index_highest:
            self.index_highest = self.running_index

    def increase(self, year, month):
        for acc in self.saving_accounts:
            acc.increase(year, month)

        for pension in self.pension_accounts:
            pension.increase(year, month)

    def withdraw(self, amount: float, year: int) -> float:
        if self.market_increase_by_year[year] < -0.20:
            for acc in self.bonds:
                amount = acc.withdraw(amount, year)

        #    Pull from 401k up to and before the 22% bracket
        #    Pull from taxable for rest (%15)
        #    Pull from Roth last
        for acc in self.post_tax_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.taxable_accounts:
            amount = acc.withdraw(amount, year)

        for acc in self.pre_tax_accounts:
            amount = acc.withdraw(amount, year)

        return amount

    def _market_is_alltime_highs(self):
        return self.running_index >= self.index_highest

    def rebalancing(self, year: int):
        if (self.bonds and
                self.market_increase_by_year[year] > 0.1):
            # Get Missing bond amount
            missing_amount = 0.0
            for acc in self.bonds:
                missing_amount += acc.missing_amount(year)

            amount = missing_amount
            for acc in self.post_tax_accounts:
                amount = acc.withdraw(amount, year)

            for acc in self.taxable_accounts:
                amount = acc.withdraw(amount, year)

            for acc in self.pre_tax_accounts:
                amount = acc.withdraw(amount, year)

            self.bonds[0].add(missing_amount - amount, year)

        for acc in self.bonds:
            acc.rebalance(year)

    def taxes(self, year: int) -> YearlyTaxes:
        if year in self.taxes_per_year:
            return self.taxes_per_year[year]
        else:
            taxable_income = self._total_taxable_income(year)
            cap_gains = self._total_cap_gains(year)
            income_taxes, income_brackets = self._calc_income_taxes(taxable_income)
            cap_gains_taxes = self._calc_cap_gains_taxes(taxable_income, cap_gains)
            yearly_taxes = YearlyTaxes(cap_gains_taxes, income_taxes, income_brackets)
            self.taxes_per_year[year] = yearly_taxes

            return yearly_taxes

    def _are_markets_good(self, year: int):
        return self.market_increase_by_year[year] > 0

    def _calc_cap_gains_taxes(self, taxable_income: float, total_cap_gains: float) -> float:
        if taxable_income > self.cap_gains_tax_brackets.brackets[0].max_income:
            return total_cap_gains * self.cap_gains_tax_brackets.brackets[1].percentage
        else:
            cap_under_first_bracket = \
                min(self.cap_gains_tax_brackets.brackets[0].max_income - taxable_income, total_cap_gains)
            cap_over_first_bracket = total_cap_gains - cap_under_first_bracket
            return cap_over_first_bracket * self.cap_gains_tax_brackets.brackets[1].percentage

    def _calc_income_taxes(self, taxable_income: float) -> Tuple[float, List[YearlyTaxBracket]]:
        taxes = 0.0
        previous_max = 0.0
        taxable_income_after_deductions = taxable_income - self.standard_deductions.amount
        if taxable_income_after_deductions < 0.0:
            yearly_brackets = [YearlyTaxBracket(bracket, 0) for bracket in self.income_tax_brackets.brackets]
            return 0.0, yearly_brackets

        yearly_brackets = []
        for bracket in self.income_tax_brackets.brackets:
            if taxable_income_after_deductions > bracket.max_income:
                taxes += (bracket.max_income - previous_max) * bracket.percentage
                previous_max = bracket.max_income
                yearly_brackets.append(YearlyTaxBracket(bracket, bracket.max_income))
            else:
                amount_bracket = taxable_income_after_deductions - previous_max
                if amount_bracket > 0:
                    taxes += amount_bracket * bracket.percentage
                    yearly_brackets.append(YearlyTaxBracket(bracket, amount_bracket))
                else:
                    yearly_brackets.append(YearlyTaxBracket(bracket, 0))
                previous_max = bracket.max_income

        return taxes, yearly_brackets

    def _total_taxable_income(self, year: int) -> float:
        amount = 0.0
        for acc in self.taxable_accounts:
            amount += acc.taxable_income(year)

        for acc in self.post_tax_accounts:
            amount += acc.taxable_income(year)

        for acc in self.pre_tax_accounts:
            amount += acc.taxable_income(year)

        for acc in self.pension_accounts:
            amount += acc.taxable_income(year)

        bond_amount = 0.0
        for acc in self.bonds:
            bond_amount += acc.taxable_income(year)
        amount += bond_amount

        return amount

    def _total_cap_gains(self, year: int) -> float:
        amount = 0.0
        for acc in self.saving_accounts:
            amount += acc.cap_taxable_income(year)

        return amount
