import csv
import datetime


def get_s_p_500_year_rate(start_year: int, historic_year: int):
    year_to_rate = {}
    future_year = start_year
    with open("s_p_500.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1

    return year_to_rate


