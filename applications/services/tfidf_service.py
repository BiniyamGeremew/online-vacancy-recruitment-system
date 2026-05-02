"""
TF-IDF Similarity Service
Calculates semantic similarity between job descriptions and CV text using TF-IDF.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_tfidf_similarity(job_description, cv_text):
    """
    Calculate TF-IDF similarity between job description and CV text.

    Args:
        job_description (str): Job requirements/description text
        cv_text (str): CV/resume text content

    Returns:
        float: Similarity score between 0-100
    """
    if not job_description or not cv_text:
        return 0.0

    # Clean and prepare texts
    job_text = _clean_text(job_description)
    cv_clean_text = _clean_text(cv_text)

    if not job_text or not cv_clean_text:
        return 0.0

    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,  # Limit features for better performance
            ngram_range=(1, 2)  # Include unigrams and bigrams
        )

        # Fit and transform texts
        tfidf_matrix = vectorizer.fit_transform([job_text, cv_clean_text])

        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # Get similarity score between job and CV (index 0 vs 1)
        similarity_score = similarity_matrix[0][1]

        # Convert to 0-100 scale
        return round(float(similarity_score) * 100, 2)

    except Exception as e:
        # Return 0 if calculation fails
        return 0.0


def _clean_text(text):
    """
    Clean and preprocess text for TF-IDF analysis.

    Args:
        text (str): Raw text

    Returns:
        str: Cleaned text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace
    text = ' '.join(text.split())

    # Basic cleaning - remove special characters but keep alphanumeric and spaces
    import re
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # Remove extra whitespace again
    text = ' '.join(text.split())

    return text