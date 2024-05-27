import tax_bracket
from typing import List
from tax_deductions import StandardDeductions


def _compound_monthly_interest(annual_rate):
    return (1 + annual_rate) ** (1 / 12) - 1


class Account:
    def __init__(self, name: str, amount: float, inflate_percent: float,
                 year: int, month: int):
        self.amount = float(amount)
        self.name = str(name)
        self.inflate_percent = inflate_percent
        self.date = year * 12 + (month - 1)
        self.withdrawn_per_year = {}
        self.added_per_year = {}
        self.inflate_percent_by_year = {}

    def __str__(self) -> str:
        return f"{self.name}: ${self.amount:,.2f}"

    def csv_header(self) -> str:
        return f";{self.name};{self.name}-pay"

    def csv_values(self, year: int) -> str:
        return f";${self.amount:,.2f};${self.withdraw_by_year(year) -  self.added_per_year.get(year, 0):,.2f}"

    def increase(self, year: int, month: int):
        current_date = year * 12 + (month - 1)
        while self.date < current_date:
            self.amount *= (1.0 + _compound_monthly_interest(self._inflate_percent(year)))
            self.date += 1

    def set_inflate_percent_by_year(self, inflate_percent_by_year):
        self.inflate_percent_by_year = inflate_percent_by_year

    def _inflate_percent(self, year):
        return self.inflate_percent_by_year.get(year, self.inflate_percent)

    def taxable_income(self, year: int) -> float:
        return 0.0

    def cap_taxable_income(self, year: int) -> float:
        return 0.0

    def withdraw_by_year(self, year: int) -> float:
        w = self.withdrawn_per_year.get(year, 0.0)
        return w if w >= 0.0 else 0.0

    def add(self, amount: float, year: int):
        self.added_per_year[year] = amount
        self.amount += amount
        withdrawn = self.withdrawn_per_year.get(year, 0)
        if withdrawn - amount <= 0:
            self.withdrawn_per_year[year] = 0
        else:
            self.withdrawn_per_year[year] -= amount

    def withdraw(self, withdraw_amount: float, year: int) -> float:
        if withdraw_amount < 0.0:
            raise Exception(f"can not withdraw negative amounts: withdraw_amount: ${withdraw_amount:,.2f}")
        if withdraw_amount > self.amount:
            left_over = withdraw_amount - self.amount
            self.amount = 0
            self.withdrawn_per_year[year] = (withdraw_amount - left_over) + self.withdrawn_per_year.get(year, 0)
            return left_over
        else:
            self.amount -= withdraw_amount
            self.withdrawn_per_year[year] = withdraw_amount + self.withdrawn_per_year.get(year, 0)
            return 0.0

    def total_taxable_pension_payments(self, amount: float, year: int):
        pass


class PreTax401k(Account):
    def __init__(self, name: str, amount: float, min_year: int,
                 inflate_percent: float, start_year: int, start_month: int):
        super(PreTax401k, self).__init__(name, amount, inflate_percent, start_year, start_month)
        self.min_year = min_year

    def withdraw(self, withdraw_amount: float, year: int) -> float:
        if year >= self.min_year:
            return super().withdraw(withdraw_amount, year)
        else:
            return withdraw_amount  # left over


class Taxable(Account):

    def __init__(self, name: str, amount: float, inflate_percent: float, start_year: int, start_month: int):
        super(Taxable, self).__init__(name, amount, inflate_percent, start_year, start_month)

    def cap_taxable_income(self, year: int) -> float:
        return self.withdraw_by_year(year) * 0.60


class TaxableWithBasis:

    def __init__(self, name: str, amount_basis: float, amount_gains: float, inflate_percent: float, start_year: int, start_month: int):
        self.amount_basis = float(amount_basis)
        self.amount_gains = float(amount_gains)
        self.name = str(name)
        self.inflate_percent = inflate_percent
        self.date = start_year * 12 + (start_month - 1)
        self.withdrawn_per_year = {}
        self.added_per_year = {}
        self.inflate_percent_by_year = {}

    def _total_amount(self):
        return self.amount_basis + self.amount_gains

    def __str__(self) -> str:
        return f"{self.name}: ${self._total_amount():,.2f}"

    def csv_header(self) -> str:
        return f";{self.name}-basis;{self.name}-gains;{self.name}-total;{self.name}-pay"

    def csv_values(self, year: int) -> str:
        return f";${self.amount_basis:,.2f};${self.amount_gains:,.2f};${self._total_amount():,.2f};${self.withdraw_by_year(year) -  self.added_per_year.get(year, 0):,.2f}"

    def increase(self, year: int, month: int):
        current_date = year * 12 + (month - 1)
        while self.date < current_date:
            self.amount_gains += self._total_amount() * _compound_monthly_interest(self._inflate_percent(year))
            self.date += 1

    def set_inflate_percent_by_year(self, inflate_percent_by_year):
        self.inflate_percent_by_year = inflate_percent_by_year

    def _inflate_percent(self, year):
        return self.inflate_percent_by_year.get(year, self.inflate_percent)

    def taxable_income(self, year: int) -> float:
        return 0.0

    def cap_taxable_income(self, year: int) -> float:
        if self.withdraw_by_year(year) > 0 and self._total_amount() > 0:
            percentage_gains = self.amount_gains / (self.amount_basis + self.amount_gains)
            return self.withdraw_by_year(year) * percentage_gains
        else:
            return 0

    def withdraw_by_year(self, year: int) -> float:
        w = self.withdrawn_per_year.get(year, 0.0)
        return w if w >= 0.0 else 0.0

    def add(self, amount: float, year: int):
        self.added_per_year[year] = amount
        self.amount_basis += amount
        withdrawn = self.withdrawn_per_year.get(year, 0)
        if withdrawn - amount <= 0:
            self.withdrawn_per_year[year] = 0
        else:
            self.withdrawn_per_year[year] -= amount

    def withdraw(self, withdraw_amount: float, year: int) -> float:
        if withdraw_amount < 0.0:
            raise Exception(f"can not withdraw negative amounts: withdraw_amount: ${withdraw_amount:,.2f}")
        if withdraw_amount > self._total_amount():
            left_over = withdraw_amount - self._total_amount()
            self.amount_basis = 0
            self.amount_gains = 0
            self.withdrawn_per_year[year] = (withdraw_amount - left_over) + self.withdrawn_per_year.get(year, 0)
            return left_over
        else:
            percentage_gains = self.amount_gains/(self.amount_basis + self.amount_gains)
            self.amount_gains -= percentage_gains * withdraw_amount
            self.amount_basis -= (1 - percentage_gains) * withdraw_amount
            self.withdrawn_per_year[year] = withdraw_amount + self.withdrawn_per_year.get(year, 0)
            return 0.0

    def total_taxable_pension_payments(self, amount: float, year: int):
        pass


class RMD(object):
    factors = [27.4, 26.5, 25.6, 24.7, 23.8, 22.9, 22, 21.2, 20.3, 19.5, 18.7, 17.9,
               17.1, 16.3, 15.5, 14.8, 14.1, 13.4, 12.7, 12, 11.4, 10.8, 10.2, 9.6, 9.1,
               8.6, 8.1, 7.6, 7.1, 6.7, 6.3, 5.9, 5.5, 5.2, 4.9, 4.6, 4.3, 4.1, 3.9, 3.7,
               3.5, 3.4, 3.3, 3.1, 3.0, 2.9, 2.8, 2.7, 2.5, 2.3, 2.0]
    start_age = 75

    @classmethod
    def _get_factor(cls, age: int) -> float:
        if age < cls.start_age:
            return 0
        elif age - cls.start_age >= len(cls.factors):
            return cls.factors[-1]
        else:
            return cls.factors[age - cls.start_age]

    @classmethod
    def get_min_yearly_withdraw(cls, account_amount: float, age: int):
        if age < cls.start_age:
            return 0
        else:
            factor = cls._get_factor(age)
            return account_amount / factor


class PostTax401k(Account):

    def __init__(self, name: str, amount: float, born_year: int,
                 inflate_percent: float, start_year: int, start_month: int, min_age: int = 60):
        super(PostTax401k, self).__init__(name, amount, inflate_percent, start_year, start_month)
        self.born_year = born_year
        self.min_age = min_age
        self.rmd_by_year = {}

    def withdraw(self, withdraw_amount: float, year: int) -> float:
        if year - self.born_year >= self.min_age:
            return super().withdraw(withdraw_amount, year)
        else:
            return withdraw_amount

    def conversion(self, withdraw_amount: float, year: int) -> float:
        return super().withdraw(withdraw_amount, year)

    def taxable_income(self, year: int) -> float:
        return self.withdraw_by_year(year)

    def required_yearly_withdraw(self, year: int) -> float:
        if year not in self.rmd_by_year:
            age = year - self.born_year
            self.rmd_by_year[year] = RMD.get_min_yearly_withdraw(self.amount, age)

        return self.rmd_by_year[year]


class PostTax401kRateLimit(object):
    logging = False

    def __init__(self, name: str, accounts: List[PostTax401k],
                 income_tax_brackets: tax_bracket.TaxBracketCollection,
                 standard_deductions: StandardDeductions,
                 max_tax_percent: float = 0.15,
                 percent_over_max: float = 0.3):
        self.name = name
        self.accounts = accounts
        self.income_tax_brackets = income_tax_brackets
        self.max_tax_percent = max_tax_percent
        self.standard_deductions = standard_deductions
        self.pension_payment_by_year = {}
        self.percent_over_max = percent_over_max

    def csv_header(self) -> str:
        output = ""
        for acc in self.accounts:
            output += f"{acc.csv_header()}"
            output += f";{acc.name}-rmd"
        return output

    def total_taxable_pension_payments(self, amount: float, year: int):
        self.pension_payment_by_year[year] = amount

    def csv_values(self, year: int) -> str:
        output = ""
        for acc in self.accounts:
            output += f"{acc.csv_values(year)}"
            output += f";${acc.required_yearly_withdraw(year):,.2f}"

        return output

    def increase(self, year: int, month: int):
        for acc in self.accounts:
            acc.increase(year, month)

    def conversion(self, amount: float, year: int) -> float:
        withdraw_amount = amount
        for acc in self.accounts:
            withdraw_amount = acc.conversion(withdraw_amount, year)

        return withdraw_amount

    def _withdraw_rmd(self, withdraw_amount: float, year: int) -> float:
        max_low_tax_bracket = self._max_low_tax_bracket()
        required_yearly_withdraw = self.required_yearly_withdraw(year)
        already_withdraw = self.withdrawn_per_year(year)
        self._log(f"({year}) (${withdraw_amount:,.2f}) max_low_tax_bracket: {max_low_tax_bracket:,.2f} required_yearly_withdraw: {required_yearly_withdraw:,.2f} already_withdraw:{already_withdraw:,.2f}")
        if required_yearly_withdraw > 0.0:
            can_withdraw = min(max(required_yearly_withdraw - already_withdraw, 0), withdraw_amount)
            amount_left = can_withdraw
            for acc in self.accounts:
                if acc.required_yearly_withdraw(year) > acc.withdraw_by_year(year):
                    required_amount_left = acc.required_yearly_withdraw(year) - acc.withdraw_by_year(year)
                    if amount_left > required_amount_left:
                        amount_left = acc.withdraw(required_amount_left, year) + (amount_left-required_amount_left)
                        self._log(f"- 1({acc.name}) can_withdraw: {can_withdraw:,.2f} amount_left: {amount_left:,.2f} withdrawn/required_amount_left: {required_amount_left:,.2f} ")
                    else:
                        w = amount_left
                        amount_left = acc.withdraw(w, year)
                        self._log(f"- 2({acc.name}) can_withdraw: {can_withdraw:,.2f} amount_left: {amount_left:,.2f} withdrawn: {w:,.2f} required_amount_left: {required_amount_left:,.2f} ")
            withdraw_amount = amount_left + (withdraw_amount - can_withdraw)

        return withdraw_amount

    def withdraw(self, withdraw_amount: float, year: int) -> float:
        max_low_tax_bracket = self._max_low_tax_bracket()
        already_withdraw = self.withdrawn_per_year(year)
        max_amount_to_withdraw = max_low_tax_bracket + self.standard_deductions.amount
        max_amount_to_withdraw = max_amount_to_withdraw * (1 + self.percent_over_max)
        total_taxable_income = already_withdraw + self.pension_payment_by_year.get(year, 0)

        left_over = self._withdraw_rmd(withdraw_amount, year)

        total_taxable_income = total_taxable_income + (withdraw_amount - left_over)

        self._log(f"- wa_after_rmd: {left_over:,.2f}")
        if total_taxable_income + left_over < max_amount_to_withdraw:
            for acc in self.accounts:
                w = left_over
                left_over = acc.withdraw(w, year)
                self._log(f"- aw + wa < max ({acc.name}) withdrawn: {w:,.2f} left_over: {left_over:,.2f}")
            return left_over
        else:
            can_withdraw = min(max(max_amount_to_withdraw - total_taxable_income, 0), left_over)
            amount_left = can_withdraw
            for acc in self.accounts:
                w = amount_left
                amount_left = acc.withdraw(w, year)
                self._log(f"- aw + wa >= max ({acc.name}) withdrawn: {w:,.2f} left_over: {amount_left:,.2f} can_withdraw: {can_withdraw:,.2f}")
            return amount_left + (left_over - can_withdraw)

    @classmethod
    def _log(cls, message: str):
        if cls.logging:
            print(message)

    def withdrawn_per_year(self, year) -> float:
        total = 0
        for acc in self.accounts:
            total += acc.withdrawn_per_year.get(year, 0)
        return total

    def taxable_income(self, year: int) -> float:
        amount = 0
        for acc in self.accounts:
            amount += acc.taxable_income(year)
        return amount

    def cap_taxable_income(self, year: int) -> float:
        return 0.0

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
