from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def rank_repositories(main_prompt, repositories, n_results=10):
    print(f"Ranking {len(repositories)} repositories based on their summaries...")
    summaries = [repo['summary'] for repo in repositories]

    # Combine main prompt with summaries for TF-IDF vectorization
    texts = [main_prompt] + summaries

    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Compute cosine similarity between the main prompt and each summary
    cosine_similarities = cosine_similarity(
        tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Add similarity scores to each repository dictionary
    for i, repo in enumerate(repositories):
        repo['similarity'] = cosine_similarities[i]

    # Sort repositories based on similarity score, in descending order
    sorted_repositories = sorted(
        repositories, key=lambda x: x['similarity'], reverse=True)
    
    return sorted_repositories[:n_results]
