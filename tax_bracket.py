from typing import List
from typing import Dict


class TaxBracket(object):
    def __init__(self, max_income: float, percentage: float):
        self.max_income = max_income
        self.percentage = percentage

    def inflate(self, percent: float):
        self.max_income *= (1.0 + percent)


class TaxBracketCollection(object):
    def __init__(self, brackets: List[TaxBracket], year: int, inflate_percent_by_year: Dict[int, float]):
        self.brackets = brackets
        self.year = year
        self.inflate_percent_by_year = inflate_percent_by_year

    def csv_header(self) -> str:
        output = ""
        for bracket in self.brackets:
            output += f";{bracket.percentage:,.2f}"

        return output

    def csv(self) -> str:
        output = ""
        for bracket in self.brackets:
            output += f";${bracket.max_income:,.2f}"

        return output

    def find_closest_bracket_below_percent(self, percent: float) -> TaxBracket:
        found_bracket = None
        for bracket in self.brackets:
            if bracket.percentage <= percent:
                found_bracket = bracket

        return found_bracket

    def inflate(self, year: int):
        while self.year < year:
            self.year += 1
            for bracket in self.brackets:
                bracket.inflate(self.inflate_percent_by_year[year])


def build_current_income_tax_brackets(inflation_percent_by_year: Dict[int, float]) -> TaxBracketCollection:
    brackets = [
        TaxBracket(22000.0, 0.10),
        TaxBracket(89450.0, 0.12),
        TaxBracket(190750.0, 0.22),
        TaxBracket(364200.0, 0.24),
        TaxBracket(462500.0, 0.32),
        TaxBracket(693750.0, 0.35),
        TaxBracket(float("inf"), 0.37)
    ]
    return TaxBracketCollection(brackets=brackets, year=2023, inflate_percent_by_year=inflation_percent_by_year)


def build_current_cap_gains_tax_brackets(inflation_percent_by_year: Dict[int, float]) -> TaxBracketCollection:
    brackets = [
        TaxBracket( 89450, 0.0),
        TaxBracket(517200, 0.15),
    ]
    return TaxBracketCollection(brackets=brackets, year=2023, inflate_percent_by_year=inflation_percent_by_year)

