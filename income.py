from typing import List
import tax_bracket
import account


class Income(object):
    def payment(self, year: int) -> float:
        pass

    def inflate(self, year: int):
        pass

    def taxable_income(self, year: int) -> float:
        pass

    def increase(self, year: int, month: int):
        pass

    def predicted_yearly_taxable_income(self, year: int) -> float:
        pass


class FixedPensionIncome(Income):

    def __init__(self, name: str, monthly_payment: float,
                 inflate_percent: float, min_year: int, start_year: int):
        self.name = name
        self.monthly_payment = monthly_payment
        self.inflate_percent = inflate_percent
        self.withdrawn_per_year = {}
        self.min_year = min_year
        self.year = start_year
        self.inflate_percent_by_year = {}

    def csv_header(self) -> str:
        return ";" + self.name

    def csv_values(self, year: int) -> str:
        return f";${self.withdrawn_per_year.get(year, 0.0):,.2f}"

    def payment(self, year: int) -> float:
        if year >= self.min_year:
            self.withdrawn_per_year[year] = self.monthly_payment + self.withdrawn_per_year.get(year, 0)
            return self.monthly_payment
        return 0

    def inflate(self, year: int):
        while self.year < year:
            self.monthly_payment *= (1.0 + self._inflate_percent(year))
            self.year += 1

    def set_inflate_percent_by_year(self, inflate_percent_by_year):
        self.inflate_percent_by_year = inflate_percent_by_year

    def _inflate_percent(self, year):
        return self.inflate_percent_by_year.get(year, self.inflate_percent)

    def taxable_income(self, year: int) -> float:
        return self.withdrawn_per_year.get(year, 0.0)

    def predicted_yearly_taxable_income(self, year: int) -> float:
        if year < self.min_year:
            return 0
        future_monthly_payment = self.monthly_payment
        future_year = self.year
        while future_year < year:
            future_year += 1
            future_monthly_payment *= (1.0 + self._inflate_percent(year))
        return future_monthly_payment * 12


class SSI(FixedPensionIncome):
    def __init__(self, name: str, monthly_payment: float,
                 inflate_percent: float, min_year: int, start_year: int):
        super(SSI, self).__init__(name, monthly_payment, inflate_percent, min_year, start_year)

    # If taxable income is more than $44,000 in 2023 tax only 85%
    # assuming income more than $44,000
    # TODO: If not pulling from 401ks income will be less than $44,000
    def taxable_income(self, year: int) -> float:
        return self.withdrawn_per_year.get(year, 0.0) * 0.85

    def predicted_yearly_taxable_income(self, year: int) -> float:
        return super().predicted_yearly_taxable_income(year) * 0.85


class PostTax401ksAsPension(Income):
    def __init__(self, accounts: List[account.PostTax401k],
                 income_tax_brackets: tax_bracket.TaxBracketCollection,
                 max_tax_percent: float):
        self.name = "401ks"
        self.accounts = accounts
        self.income_tax_brackets = income_tax_brackets
        self.max_tax_percent = max_tax_percent
        self.monthly_payment = 0
        self.yearly_withdraw = {}

    def payment(self, year: int) -> float:
        monthly_amount = max(self._max_low_tax_bracket(),
                             self.required_yearly_withdraw(year)) / 12.0
        amount = monthly_amount
        for acc in self.accounts:
            amount = acc.withdraw(amount, year)

        self.monthly_payment = monthly_amount - amount
        withdraw = monthly_amount - amount
        self.yearly_withdraw[year] = withdraw + self.yearly_withdraw.get(year, 0)
        return withdraw

    def required_yearly_withdraw(self, year: int) -> float:
        amount = 0
        for acc in self.accounts:
            amount += acc.required_yearly_withdraw(year)
        return amount

    def _max_low_tax_bracket(self) -> float:
        bracket = self.income_tax_brackets.find_closest_bracket_below_percent(self.max_tax_percent)
        if not bracket:
            return 0

        return bracket.max_income

    def csv_header(self) -> str:
        output = ""
        for acc in self.accounts:
            output += f"{acc.csv_header()}"

        output += f";{self.name}-pay"
        output += f";rmd"
        return output

    def csv_values(self, year: int) -> str:
        output = ""
        for acc in self.accounts:
            output += f"{acc.csv_values(year)}"

        output += f";${self.yearly_withdraw[year]:,.2f}"
        output += f";${self.required_yearly_withdraw(year):,.2f}"
        return output

    def inflate(self, year: int):
        self.income_tax_brackets.inflate(year)

    def increase(self, year: int, month: int):
        for acc in self.accounts:
            acc.increase(year, month)

    def taxable_income(self, year: int) -> float:
        total = 0
        for acc in self.accounts:
            total += acc.taxable_income(year)

        return total

    def predicted_yearly_taxable_income(self, year: int) -> float:
        return max(self._max_low_tax_bracket(), self.required_yearly_withdraw(year))


class LumpSumPayment(object):

    def __init__(self, amount: float, year: int):
        self.amount = amount
        self.year = year
