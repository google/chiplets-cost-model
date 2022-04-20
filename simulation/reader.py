import csv

def readFile(fileName):
    input = []
    with open('inputs/' + fileName) as file:
        reader = csv.DictReader(file)
        for row in reader:
            input.append(row)
    return input
