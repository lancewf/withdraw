import csv
import datetime
from collections import defaultdict

def get_5_year_note_rate(start_year: int, historic_year: int, default_rate: float = 0.03):
    year_to_rate = defaultdict(lambda: default_rate)
    future_year = start_year
    with open("5Y_Treasury_Yields_1962_2024.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1

    historic_year = 1962
    with open("5Y_Treasury_Yields_1962_2024.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1
    return year_to_rate

def get_s_p_500_year_rate(start_year: int, historic_year: int, default_rate: float = 0.08):
    year_to_rate = defaultdict(lambda: default_rate)
    future_year = start_year
    with open("s_p_500.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1

    historic_year = 1962
    with open("s_p_500.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1

    return year_to_rate


def get_inflation_year_rate(start_year: int, historic_year: int, default_rate: float = 0.029):
    year_to_rate = defaultdict(lambda: default_rate)
    future_year = start_year
    with open("inflation.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1

    historic_year = 1962
    with open("inflation.csv", "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            date_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d").date()
            if historic_year <= date_obj.year:
                year_to_rate[future_year] = float(row[1])/100
                future_year += 1
    return year_to_rate

