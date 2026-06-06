"""
==========================================
Basic Vector Database Example
==========================================

"""

import numpy as np

class VectorDatabase:
    def encoder(self, vector):
        return np.dot(self.W, vector) + self.b

    def _cosine_similarity(self, a, b):
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return -1.0
        return float(np.dot(a, b) / denom)

    def add_entry(self, text):
        initial_vector = self.text_to_vector(text)
        encoded_vector = self.encoder(initial_vector)
        self.data[text] = encoded_vector

    def query(self, text, top_k=1):
        query_vector = self.encoder(self.text_to_vector(text))
        similarities = []
        for key, value in self.data.items():
            score = self._cosine_similarity(query_vector, value)
            similarities.append((key, score))

        similarities.sort(key=lambda x: x[1], reverse=True)
        if top_k == 1:
            return similarities[0][0] if similarities else None
        return similarities[:top_k]

    def text_to_vector(self, text):
        tokens = text.split()
        vectors = [self.word_to_vector[word] for word in tokens if word in self.word_to_vector]
        if not vectors:
            return np.zeros(self.embedding_dim)

        # Simple sentence embedding: average token vectors.
        return np.mean(vectors, axis=0)

    def __init__(self, word_to_vector, W, b):
        self.word_to_vector = word_to_vector
        self.W = W
        self.b = b
        self.embedding_dim = next(iter(word_to_vector.values())).shape[0]
        self.data = {}

vocabulary = [
    "i", "am", "happy", "sad", "not", "and", "tell", "me", "your", "name",
    "you", "are", "is", "today", "fine", "great", "bad", "weather", "sunny", "rainy", "hello",
    "bye", "thanks", "please", "friend", "python", "code", "vector", "database", "search", "query",
]

# Build a simple one-hot encoding for the vocabulary (try other embeddings)
def build_one_hot_vocab(words):
    size = len(words)
    mapping = {}
    for idx, word in enumerate(words):
        vec = np.zeros(size)
        vec[idx] = 1.0
        mapping[word] = vec
    return mapping


word_to_vector = build_one_hot_vocab(vocabulary)
W = np.eye(len(vocabulary))
b = np.zeros(len(vocabulary))


db = VectorDatabase(word_to_vector, W, b)

db.add_entry("i am happy")
db.add_entry("i am sad")
db.add_entry("you are fine")
db.add_entry("you are great")
db.add_entry("weather is sunny")
db.add_entry("weather is rainy")
db.add_entry("python code vector database")
db.add_entry("hello friend")
db.add_entry("thanks friend")
db.add_entry("please tell me your name")

# Input a text from keyboard
query = input("Enter your query: ")
result = db.query(query)
top3 = db.query(query, top_k=3)
print("Query: %s" % query)
print("Result: %s" % result)
print("Top 3: %s" % top3)
