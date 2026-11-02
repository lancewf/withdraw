from yearly_withdraw_manager import YearlyWithdrawManager
from yearly_withdraw_manager import YearlyTaxes
import scenarios


def print_year(year: int, expenses: float, manager: YearlyWithdrawManager, f, birth_year=1977):
    f.write(f'{str(year)};{year - birth_year};${expenses:,.2f}{manager.csv(year)}\n')


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

    run_with_write(2007)


def run_with_year(start_historic_year):
    manager, expenses, start_year = scenarios.buckets(start_historic_year)

    end_year = 2092

    taxes = 0.0
    withdrawn_vs_networth = 0.0
    for year in range(start_year, end_year + 1):
        expenses.inflate(year)
        manager.inflate(year)
        manager.set_total_predicted_income_taxes(year)
        # jan 1st
        yearly_income = expenses.amount(year, withdrawn_vs_networth)
        manager.pay_taxes(taxes, year)
        withdrawn_amount = 0
        for month in range(1, 13):
            monthly_income = yearly_income / 12
            manager.increase(year, month)
            pension = manager.monthly_pension(year)
            monthly_income -= pension
            if monthly_income < 0:
                manager.payment(monthly_income * -1, year)
            else:
                withdrawn_amount += monthly_income
                monthly_left_over = manager.withdraw(monthly_income, year)
                if monthly_left_over > 0:
                    return False

        if manager.networth() > 0:
            withdrawn_vs_networth = withdrawn_amount / manager.networth()
        else:
            withdrawn_vs_networth = 0.0

        manager.conversions(year)
        manager.lump_sum_payments(year)
        taxes = manager.taxes(year).total()
        manager.rebalancing(year)

    return True


def run_with_write(start_historic_year):
    manager, expenses, start_year = scenarios.buckets(start_historic_year)

    end_year = 2092

    taxes = 0.0
    with open("output/output.csv", "w") as f:
        print_header(manager, f)
        highest_evn_year = start_year
        highest_evn_percent = 0.0
        withdrawn_vs_networth = 0.0
        for year in range(start_year, end_year + 1):
            expenses.inflate(year)
            manager.inflate(year)
            manager.set_total_predicted_income_taxes(year)
            # jan 1st
            yearly_income = expenses.amount(year, withdrawn_vs_networth)
            manager.pay_taxes(taxes, year)
            withdrawn_amount = 0
            for month in range(1, 13):
                monthly_income = yearly_income / 12
                manager.increase(year, month)
                pension = manager.monthly_pension(year)
                monthly_income -= pension
                if monthly_income < 0: # extra add to accounts
                    manager.payment(monthly_income * -1, year)
                else:
                    withdrawn_amount += monthly_income
                    monthly_left_over = manager.withdraw(monthly_income, year)
                    if monthly_left_over > 0:
                        print(f'out of money year {year} {monthly_left_over}')
                        return
            withdrawn_vs_networth = withdrawn_amount / manager.networth()
            if withdrawn_vs_networth > highest_evn_percent:
                highest_evn_percent = withdrawn_vs_networth
                highest_evn_year = year

            manager.conversions(year)
            manager.lump_sum_payments(year)
            taxes = manager.taxes(year).total()
            manager.rebalancing(year)

            # Dec 31st
            print_year(year, yearly_income, manager, f, birth_year=1977)

        print(f'end networth {manager.networth():,.2f}')
        print(f'highest income/networth {highest_evn_percent*100:,.2f}% year {highest_evn_year}')

run()
