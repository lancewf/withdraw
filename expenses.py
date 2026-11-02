

class Expense(object):
    def __init__(self, initial_expense: float, year: int, cancelable: bool = False):
        self._amount = initial_expense
        self._year = year
        self._cancelable = cancelable

    def inflate(self, year: int, inflate_percent: float):
        while self._year < year:
            self._amount *= (1.0 + inflate_percent)
            self._year += 1

    def amount(self, year: int) -> float:
        return self._amount

    def cancelable(self) -> bool:
        return self._cancelable


class HousingExpense(Expense):
    def __init__(self, initial_expense: float, year: int, end_payments_year: int,
                 start_payments_year: int = 0):
        super(HousingExpense, self).__init__(initial_expense, year)
        self._payed_off_year = end_payments_year
        self._start_payments_year = start_payments_year

    def inflate(self, year: int, inflate_percent: float):
        self._year = year

    def amount(self, year: int) -> float:
        a = 0.0
        if self._start_payments_year <= year < self._payed_off_year:
            a = super().amount(year)
        return a


class EndingExpense(Expense):
    def __init__(self, initial_expense: float, year: int, end_year: int, start_year: int, cancelable: bool= False):
        super(EndingExpense, self).__init__(initial_expense, year, cancelable)
        self._end_year = end_year
        self._start_year = start_year

    def amount(self, year: int) -> float:
        if year >= self._end_year or year < self._start_year:
            return 0.0
        else:
            return super().amount(year)


class JobIncome(Expense):
    def __init__(self, initial_payment: float, year: int, start_year: int, end_year: int):
        super(JobIncome, self).__init__(initial_payment * -1, year)
        self._end_year = end_year
        self._start_year = start_year

    def amount(self, year: int) -> float:
        if year >= self._end_year or year < self._start_year:
            return 0.0
        else:
            return super().amount(year)

class Expenses(object):
    def __init__(self, expenses: [Expense], inflate_percent: float, market_rate_by_year):
        self.expenses = expenses
        self.inflate_percent = inflate_percent
        self.inflate_percent_by_year = {}
        self.market_rate_by_year = market_rate_by_year

    def inflate(self, year: int):
        for expense in self.expenses:
            expense.inflate(year, self._inflate_percent(year))

    def set_inflate_percent_by_year(self, inflate_percent_by_year):
        self.inflate_percent_by_year = inflate_percent_by_year

    def _inflate_percent(self, year):
        return self.inflate_percent_by_year.get(year, self.inflate_percent)

    def amount(self, year, withdrawn_vs_networth: float = 0.0) -> float:
        total = 0.0
        for expense in self.expenses:
            if expense.cancelable():
                if (self.market_rate_by_year[year] < -0.1 and withdrawn_vs_networth > 0.06) or withdrawn_vs_networth > 0.1:
                    # bad market year and withdraw % is high, skip non-essentials
                    total += 0
                else:
                    total += expense.amount(year)
            else:
                total += expense.amount(year)
        return total
