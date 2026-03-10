# Jesus Lopez
# 1002103351

import sys, math
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score


class MLChoice:
    # initialize values
    def __init__(self, ML, DataSet):
        self.ML = ML
        self.DataSet = DataSet

        self.alpha = 0.01
        self.cycles = 1000
        self.lambda_ = 0.01
        self.is_string = False
        self.mapping = {}
        self.k = None
        
        self.x_train, self.x_test, self.y_train, self.y_test = self.read_data()
        self.run()

    # calculating euclidean distance
    def euclidean_distance(self, x1, x2):
        distance = 0
        for i in range(len(x1)):
            distance += (x1[i] - x2[i])**2
        return math.sqrt(distance)
    
    # knn fit since there's no training phase for knn we just store the training data and labels and calculate k value
    def knn_fit(self, x_train, y_train):
        self.x = x_train
        self.y = y_train
        self.k = int(math.sqrt(len(x_train)))   
        if self.k % 2 == 0:
            self.k += 1

    
    def knn_predict(self, x_test):
        # store predictions for each test point
        prediction = []

        for test_point in x_test:
            distance =[]

            #1. Computing the distance from test point to all training points
            for i in range(len(self.x)):
                dist = self.euclidean_distance(self.x[i], test_point)
                distance.append((dist, self.y[i]))

            #2. Sort by distance
            distance.sort(key = lambda v: v[0])

            #3. select k nearest neighbors 
            k_neighbors = distance[:self.k]

            #4. majority vote
            class_vote = {}
            for _, label in k_neighbors: 
                if label in class_vote:
                    class_vote[label] += 1
                else:
                    class_vote[label] = 1

            #5. return max class
            prediction.append(max(class_vote, key = class_vote.get))
        return prediction

    def SVM_fit(self, x_train, y_train):
        
        features = x_train.shape[1]
        self.unique_labels = np.unique(y_train)
        self.weights, self.bias = [], []
        
        for c in self.unique_labels:
            # using one vs all 
            y_binary = np.where(y_train == c, 1, -1)
            w, b = np.zeros(features), 0
            
            # gradient descent
            for _ in range(self.cycles):
                for i, x_i in enumerate(x_train):
                    # constraint to be satisfied
                    if y_binary[i] * (np.dot(w, x_i) + b) >= 1:
                        # classification correct
                        w -= self.alpha * (2 * self.lambda_ * w)
                    else:
                        w -= self.alpha * (2 * self.lambda_ * w - y_binary[i] * x_i)
                        b += self.alpha * y_binary[i]

            self.weights.append(w)
            self.bias.append(b)
        
        self.weights = np.array(self.weights)
        self.bias = np.array(self.bias)
    
    def SVM_predict(self, x_test):
        # data classification
        scores = np.dot(x_test, np.array(self.weights).T) + np.array(self.bias)
        return self.unique_labels[np.argmax(scores, axis=1)]

    def read_data(self):
        # read the data
        with open(self.DataSet, 'r') as file:
            lines = file.readlines()

        start = 0
        # header check
        if any(c.isalpha() for c in lines[0].split(',')[0]):
            start = 1

        rows = []
        for line in lines[start:]:
            if line.strip():
                rows.append(line.strip().split(','))

        has_id = False
        # check which dataset we are handling to set y equal to its column
        if rows[0][1].lower() in ['m', 'b']:
            index = 1
            has_id = True  
        else: 
            index = -1
            if "iris" in self.DataSet.lower():
                has_id = True

        x = []
        y_before = []
        # formatting the data into x and y lists
        for row in rows:
            start_col = 1 if has_id else 0
            if index == 1:
                features = row[2:]
                x.append([float(value) for value in features])
                y_before.append(row[1])
            else:
                x.append([float(value) for value in row[start_col:-1]])
                y_before.append(row[-1])

        self.is_string = any(c.isalpha() for c in y_before[0])

        # convert y to numbers if it stores strings
        if self.is_string:
            unique, y_nums  = np.unique(y_before, return_inverse=True)
            y = y_nums.tolist()
            self.mapping = {num: label for num, label in enumerate(unique)}
        else:
            y = [int(float(value)) for value in y_before]

        x = np.array(x)
        y = np.array(y)

        np.random.seed(42)
        # shuffle data and split data
        shuffle = np.random.permutation(len(x))
        x = x[shuffle]
        y = y[shuffle]

        ratio = int(0.7 * len(x))
        x_train, y_train = x[:ratio], y[:ratio]
        x_test, y_test = x[ratio:], y[ratio:]

        # save copy for clean output since numpy is used
        self.raw_x_test = x_test.copy()


        # feature scale the data as breast_cancer svm is accuracy is low without it
        mean = x_train.mean(axis=0)
        std = x_train.std(axis=0)
        std[std == 0] = 1 
        x_train = (x_train - mean) / std
        x_test = (x_test - mean) / std

        return x_train, x_test, y_train, y_test
    
    def run(self):
        # if model is knn we follow its steps
        if self.ML == "knn":
            self.knn_fit(self.x_train, self.y_train)
            prediction = self.knn_predict(self.x_test)
            accuracy = accuracy_score(self.y_test, prediction)

            sklearn_model = KNeighborsClassifier(n_neighbors=self.k)
            sklearn_model.fit(self.x_train, self.y_train)
            sklearn_accuracy = accuracy_score(self.y_test, sklearn_model.predict(self.x_test))
        # if model is svm we follow its steps
        elif self.ML == "svm":
            self.SVM_fit(self.x_train, self.y_train)
            prediction = self.SVM_predict(self.x_test)
            accuracy = accuracy_score(self.y_test, prediction)
            

            sklearn_model = SVC(kernel='linear')
            sklearn_model.fit(self.x_train, self.y_train)
            sklearn_accuracy = accuracy_score(self.y_test, sklearn_model.predict(self.x_test))
        # else we print an error message
        else:
            print("Invalid ML choice. Please choose 'knn' or 'svm'.")
            return
        # printing the sample output from assignment instruction
        print(f"DataSet: {self.DataSet}")
        print(f"Machine Learning Algorithm Chosen: {self.ML.upper()}")
        print(f"Accuracy of Training (Scratch): {accuracy * 100:.0f}%")
        print(f"Accuracy of ScikitLearn Function: {sklearn_accuracy * 100:.0f}%")

        prediction_point = [round(float(value), 5) for value in self.raw_x_test[0]]
        point = "[" + ",".join(str(p) for p in prediction_point) + "]"
        print(f"\nPrediction Point: {point}")

        # changing numbers to strings if the dataset has strings
        if self.is_string:
            pred = self.mapping[prediction[0]]
            actual = self.mapping[self.y_test[0]]
        else:
            pred = prediction[0]
            actual = self.y_test[0]
            
        print(f"Predicted Class: {pred}")
        print(f"Actual Class: {actual}")
# check against wrong arguments
if len(sys.argv) != 3:
    print("Usage: python MLChoice.py <ML> <DataSet>")
    sys.exit(1)

# call the model with command line arguments
ml_choice = sys.argv[1].lower()
data_set_choice = sys.argv[2] 

model = MLChoice(ml_choice, data_set_choice)