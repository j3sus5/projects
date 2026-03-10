import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

class RegressionModel:

    # initialize values
    def __init__(self, alpha, cycles):
        self.alpha = alpha
        self.cycles = cycles
        self.weights = None
        self.bias = 0
        self.cost = []
        self.model = None


    def linear_fit(self, x, y):
        self.model = "linear"
        m, n = x.shape
        self.weights = np.zeros(n)
        self.bias = 0
        self.cost = []
        # compute gradient descent 
        for _ in range(self.cycles):
            y_hat= np.dot(x, self.weights) + self.bias

            # mean squared error cost function
            cost = np.mean((y_hat - y) ** 2)
            self.cost.append(cost)

            # compute gradients
            dw = (1 / m) * np.dot(x.T, (y_hat - y))
            db = (1 / m) * np.sum(y_hat - y)

            # update weights and bias
            self.weights -= self.alpha * dw
            self.bias -= self.alpha * db

    def logistic_fit(self, x, y):
        self.model = "logistic"
        m, n = x.shape
        self.weights = np.zeros(n)
        self.bias = 0
        self.cost = []
        
        # compute gradient descent
        for _ in range(self.cycles):
            # z = wx + b
            z = np.dot(x, self.weights) + self.bias
            # sigmoid function
            y_hat = 1 / (1 + np.exp(-z))

            # log loss function
            cost = -np.mean(y * np.log(y_hat) + (1 - y) * np.log(1 - y_hat))
            self.cost.append(cost) 

            # compute gradients
            dw = (1 / m) * np.dot(x.T, (y_hat - y))
            db = (1 / m) * np.sum(y_hat - y)

            # update weights and bias
            self.weights -= self.alpha * dw
            self.bias -= self.alpha * db

    def predict(self, x):
        # compute z = wx + b
        z = np.dot(x, self.weights) + self.bias

        # return value for linear regression, and class label for logistic regression
        if self.model == "linear":
            return z
        prob = 1 / (1 + np.exp(-z))
        return np.array([1 if p >= 0.5 else 0 for p in prob])
    # cost values list
    def get_cost(self):
        return self.cost

def run_csv(filename):
    # read file
    with open(filename, 'r') as file:
        lines = file.readlines()

    header = lines[0].strip().split(',')
    rows = []
    # store data 
    for line in lines[1:]:
        rows.append(line.strip().split(','))

    check_binary = [row[-1] for row in rows]
    # pass alpha and cycles
    model = RegressionModel(0.01, 1000)

    # if the last column is not binary, then we will do linear regression
    if not all(cb in ('0', '1') for cb in check_binary):
        # unique complaint category
        unique = set()
        for row in rows:
            unique.add(row[1])

        unique = sorted(list(unique))

        # map complaint to index
        categories = {category: i for i, category in enumerate(unique)} 
        
        x = []
        y = []
        for row in rows:
            # turn into binary vector for each category
            category = [0] * len(unique)
            category[categories[row[1]]] = 1
            x.append(category)
            y.append(float(row[3]))
        
        x = np.array(x)
        y = np.array(y)
        # shuffle data before splitting into train and test sets
        shuffle = np.random.permutation(len(x))
        x = x[shuffle]
        y = y[shuffle]
        # split 70% for training and 30% for testing
        ratio = int(0.7 * len(y))

        x_train  = x[:ratio]
        y_train = y[:ratio]

        x_test = x[ratio:]
        y_test = y[ratio:]
        # feature scaling
        mean = x_train.mean(axis=0)
        std = x_train.std(axis=0)
        std[std == 0] = 1
        x_train = (x_train - mean) / std
        x_test = (x_test - mean) / std
        

        model.linear_fit(x_train, y_train)

        # prediction on test set, mse computation, and R^2 score computation
        y_hat = model.predict(x_test)
        mse = np.mean((y_hat - y_test) ** 2)
        denominator = np.sum((y_test - np.mean(y_test)) ** 2)
        r_squared = 1 - np.sum((y_test - y_hat) ** 2) / denominator if denominator > 0 else 0

        print("\nlinear regression estimated parameters:")
        print(f'weights: {model.weights}\nbias: {model.bias}\ncost: {model.get_cost()[-1]}')
        print("linear evaluation:")
        print(f'mean squared error: {mse}')
        print(f'R^2 score: {r_squared}\n')

        # cost plot
        plt.plot(model.get_cost()) 
        plt.title('Cost over Iterations (linear regression)')
        plt.xlabel('Iteration')
        plt.ylabel('Cost')
        plt.show()
        
    else:

        x = []
        y = []
        # store data 
        for row in rows:
            x.append([float(row[0]), float(row[1]), float(row[2])])
            y.append(int(row[3]))

        x = np.array(x)
        y = np.array(y, dtype=int)

        # shuffle data
        shuffle = np.random.permutation(len(x))
        x = x[shuffle]
        y = y[shuffle]
        
        # train 70% and test 30%
        ratio = int(0.7 * len(y))

        x_train  = x[:ratio]
        y_train = y[:ratio]

        x_test = x[ratio:]
        y_test = y[ratio:]

        # feature scaling
        mean = x_train.mean(axis=0)
        std = x_train.std(axis=0)
        std[std == 0] = 1
        x_train = (x_train - mean) / std
        x_test = (x_test - mean) / std

        # train logistic model
        model.logistic_fit(x_train, y_train)
        print("logistic regression estimated parameters:")
        print(f'weights: {model.weights}\nbias: {model.bias}\ncost: {model.get_cost()[-1]}')
        
        y_hat = model.predict(x_test)

        tp = tn = fp = fn = 0
        # compute accuracy, precision, recall, and f1-score 
        for predict, actual in zip(y_hat, y_test):
            if predict == 1 and actual == 1:
                tp += 1
            elif predict == 0 and actual == 0:
                tn += 1 
            elif predict == 1 and actual == 0:
                fp += 1
            elif predict == 0 and actual == 1:
                fn += 1    
                
        accuracy = (tp + tn) / len(y_test) 
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print("logistic evaluation:")
        print(f'accuracy: {accuracy}')
        print(f'precision: {precision}')
        print(f'recall: {recall}')
        print(f'f1-score: {f1_score}')

        # cost plot
        plt.plot(model.get_cost()) 
        plt.title('Cost over Iterations (logistic regression)')
        plt.xlabel('Iteration')
        plt.ylabel('Cost')
        plt.show()


run_csv("CustomerService.csv")

run_csv("ModifiedHeartDisease.csv")