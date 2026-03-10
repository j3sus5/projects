import math
from collections import Counter, defaultdict

class MultiNomialNaiveBayes:

    def __init__(self):
        self.vocab = set()
        self.class_priors = {}
        self.word_likelihoods = defaultdict(dict)
        self.class_word_counts = defaultdict(Counter)
        self.class_totals = defaultdict(int)

    def tokenize(self, text):
        return text.lower().split()
    
    def fit(self, documents, labels):
        total_docs = len(documents)
        class_counts = Counter(labels)

        for label in class_counts:
            self.class_priors[label] = class_counts[label] / total_docs

        for doc, label in zip(documents, labels):
            words = self.tokenize(doc)
            self.vocab.update(words)
            self.class_word_counts[label].update(words)
            self.class_totals[label] += len(words)

        V = len(self.vocab)

        for label in class_counts:
            for word in self.vocab:
                count = self.class_word_counts[label][word]
                self.word_likelihoods[label][word] = (count + 1) / (self.class_totals[label] + V)

    def predict(self, document):
        words = self.tokenize(document)
        scores = {}

        for label in self.class_priors:
            score = math.log(self.class_priors[label])
            for word in words:
                if word not in self.vocab:
                    continue
                score += math.log(self.word_likelihoods[label][word])
            scores[label] = score

        return max(scores, key = scores.get)

docs = []
labels = []

with open("reviews.csv", 'r') as file:
    for line in file:
        line = line.strip()
        review, label = line.split(',')
        docs.append(review)
        labels.append(label)

# 0.7 for training and 0.3 for testing
ratio = int(0.7 * len(docs))

train_doc = docs[:ratio]
train_label = labels[:ratio]

test_doc = docs[ratio:]
test_label = labels[ratio:]



model = MultiNomialNaiveBayes()

model.fit(train_doc, train_label)

predictions = []

for review in test_doc:
    predictions.append(model.predict(review))

correct = 0

for label, predict_label in zip(test_label, predictions):
    if label == predict_label:
        correct += 1

accuracy = correct / len(test_label)

print(f'test accuracy: {accuracy}')

data = [
    "I had a terrible experience with this company", 
    "This is a great company with excellent customer service", 
    "I was really disappointed with this product", 
    "The service is too expensive for what it offers"
]

print("\nprediction output\n")

for index, review in enumerate(data):
    prediction = model.predict(review)
    print(f'review {index + 1}: {prediction}')

