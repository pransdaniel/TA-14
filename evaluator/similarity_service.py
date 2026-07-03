from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')


def calculate_similarity(reference, essay):
    docs = [reference, essay]

    id_stopwords = stopwords.words('indonesian')

    vectorizer = CountVectorizer(
        lowercase=True,
        ngram_range=(1, 1),
        stop_words=id_stopwords
    )

    tf_matrix = vectorizer.fit_transform(docs)
    similarity = cosine_similarity(tf_matrix[0:1], tf_matrix[1:2])[0][0]

    return float(similarity)