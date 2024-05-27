from yearly_withdraw_manager import YearlyWithdrawManager
from yearly_withdraw_manager import YearlyTaxes
import scenarios


def print_year(year: int, expenses: float, manager: YearlyWithdrawManager, f):
    f.write(f'{str(year)};{year - 1977};${expenses:,.2f}{manager.csv(year)}\n')


def print_header(manager: YearlyWithdrawManager, f):
    f.write(f"year;age;income{manager.csv_header()}\n")


def run():
    # count = 0
    # total = 0
    # for year in range(1960, 2025):
    #     if run_with_year(year):
    #         count += 1
    #     total += 1
    #
    # print(f"success {count}/{total} {count/total * 100:.1f}%")

    run_with_write(2025)


def run_with_year(start_historic_year):
    manager, expenses, start_year = scenarios.inorder_rate_limit(start_historic_year)

    end_year = 2092

    taxes = 0.0
    for year in range(start_year, end_year + 1):
        expenses.inflate(year)
        manager.inflate(year)
        manager.set_total_predicted_income_taxes(year)
        # jan 1st
        yearly_income = expenses.amount(year)
        manager.pay_taxes(taxes, year)
        for month in range(1, 13):
            monthly_income = yearly_income / 12
            manager.increase(year, month)
            pension = manager.monthly_pension(year)
            monthly_income -= pension
            if monthly_income < 0:
                return False
            monthly_left_over = manager.withdraw(monthly_income, year)
            if monthly_left_over > 0:
                return False

        manager.conversions(year)
        manager.lump_sum_payments(year)
        taxes = manager.taxes(year).total()

    return True


def run_with_write(start_historic_year):
    manager, expenses, start_year = scenarios.inorder_rate_limit(start_historic_year)

    end_year = 2092

    taxes = 0.0
    with open("output/output.csv", "w") as f:
        print_header(manager, f)
        for year in range(start_year, end_year + 1):
            expenses.inflate(year)
            manager.inflate(year)
            manager.set_total_predicted_income_taxes(year)
            # jan 1st
            yearly_income = expenses.amount(year)
            manager.pay_taxes(taxes, year)
            for month in range(1, 13):
                monthly_income = yearly_income / 12
                manager.increase(year, month)
                pension = manager.monthly_pension(year)
                monthly_income -= pension
                if monthly_income < 0:
                    print(f"pension payment is more than needed income {pension:,.2f}")
                    return
                monthly_left_over = manager.withdraw(monthly_income, year)
                if monthly_left_over > 0:
                    print(f'out of money year {year} {monthly_left_over}')
                    return

            manager.conversions(year)
            manager.lump_sum_payments(year)
            taxes = manager.taxes(year).total()

            # Dec 31st
            print_year(year, expenses.amount(year), manager, f)


run()
