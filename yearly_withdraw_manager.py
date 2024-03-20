import account
import tax_bracket
import income
import tax_deductions


class Expenses(object):
    def __init__(self, initial_expenses: float, initial_year: int, inflate_percent: float):
        self.amount = initial_expenses
        self.year = initial_year
        self.inflate_percent = inflate_percent

    def inflate(self, year: int):
        while self.year < year:
            self.amount *= (1.0 + self.inflate_percent)
            self.year += 1


class YearlyTaxes:
    def __init__(self, cap_gains_taxes: float, income_taxes: float):
        self.cap_gains_taxes = cap_gains_taxes
        self.income_taxes = income_taxes

    def total(self) -> float:
        return self.cap_gains_taxes + self.income_taxes

    def csv(self) -> str:
        return f";${self.cap_gains_taxes:,.2f};${self.income_taxes:,.2f};${self.total():,.2f}"


class YearlyWithdrawManager:

    def __init__(self,
                 post_tax_accounts: [account.Account],
                 pre_tax_accounts: [account.Account] ,
                 taxable_accounts: [account.Account],
                 pension_accounts: [income.Income],
                 income_tax_brackets: tax_bracket.TaxBracketCollection,
                 cap_gains_tax_brackets: tax_bracket.TaxBracketCollection,
                 standard_deductions: tax_deductions.StandardDeductions
                 ):
        self.income_tax_brackets = income_tax_brackets
        self.cap_gains_tax_brackets = cap_gains_tax_brackets
        self.post_tax_accounts = post_tax_accounts
        self.pre_tax_accounts = pre_tax_accounts
        self.taxable_accounts = taxable_accounts
        self.pension_accounts = pension_accounts
        self.saving_accounts = taxable_accounts + post_tax_accounts + pre_tax_accounts
        self.taxes_per_year = {}
        self.standard_deductions = standard_deductions

    def csv_header(self) -> str:
        output = ""
        for acc in self.saving_accounts:
            output += f"{acc.csv_header()}"

        for acc in self.pension_accounts:
            output += f"{acc.csv_header()}"

        for bracket in self.income_tax_brackets.brackets:
            output += f";{bracket.percentage}"

        for bracket in self.cap_gains_tax_brackets.brackets:
            output += f";{bracket.percentage}"

        output += ";standed"

        return output

    def csv(self, year: int) -> str:
        output = ""
        for acc in self.saving_accounts:
            output += f"{acc.csv_values(year)}"

        for acc in self.pension_accounts:
            output += f"{acc.csv_values(year)}"

        for bracket in self.income_tax_brackets.brackets:
            output += f";${bracket.max_income:,.2f}"

        for bracket in self.cap_gains_tax_brackets.brackets:
            output += f";${bracket.max_income:,.2f}"

        output += f";${self.standard_deductions.amount:,.2f}"

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
            income_taxes = self._calc_income_taxes(taxable_income)
            cap_gains_taxes = self._calc_cap_gains_taxes(taxable_income, cap_gains)
            yearly_taxes = YearlyTaxes(cap_gains_taxes, income_taxes)
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

    def _calc_income_taxes(self, taxable_income: float) -> float:
        taxes = 0.0
        previous_max = 0.0
        taxable_income_after_deductions = taxable_income - self.standard_deductions.amount
        if taxable_income_after_deductions < 0.0:
            return 0.0

        for bracket in self.income_tax_brackets.brackets:
            if taxable_income_after_deductions > bracket.max_income:
                taxes += (bracket.max_income - previous_max) * bracket.percentage
                previous_max = bracket.max_income
            else:
                taxes += (taxable_income_after_deductions - previous_max) * bracket.percentage
                return taxes

        taxes += (taxable_income_after_deductions - previous_max) * self.income_tax_brackets.brackets[-1].percentage

        return taxes

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

