def calculation(data):
    mean = 0
    variance = 0

    for value in data:
        mean += float(value)
        variance += float(value) ** 2

    mean /= len(data)
    variance /= len(data)
    
    variance -= mean ** 2
    standard_deviation = variance ** 0.5

    print("Mean:", round(mean, 4))
    print("standard deviation:", round(standard_deviation, 4))

text = ""
while True:
    text = input("Enter file (type quit to exit): ").strip()
    if text.lower() == "quit":
        break
    with open(text, 'r') as file:
        data = file.readlines()

    calculation(data)