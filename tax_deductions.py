
class StandardDeductions:
    def __init__(self):
        self.amount = 27700
        self.year = 2023
        self.inflation_rate = 0.029

    def inflate(self, year: int):
        while self.year < year:
            self.year += 1
            self.amount *= (1.0 + self.inflation_rate)
