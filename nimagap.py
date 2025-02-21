class Car:
    __name1 = "Hello"
    def __init__(self, name):
        Car.name = name

Car.name1 = "Salom"
print(Car.name1)
