from app.config.config import read_config_json

def load_and_sort_vocab_list(file_path: str) -> list[str]:
    """Load and sort the vocabulary list from a JSON file."""
    vocab_list = read_config_json(file_path)
    return sorted([word.lower() for word in vocab_list])  # Normalize case and sort

# Preload and sort the vocab list
vocab_list = load_and_sort_vocab_list("vocab.json")

def get_vocab_list(query: str) -> list[str]:
    """
    Return a list of up to 10 matching words based on the query string.
    Prioritize prefix matches, then include substring matches if needed.
    """
    query = query.strip().lower()  # Normalize query
    if not query:
        return vocab_list[:10]  # Return first 10 words if query is empty

    matched_prefix = []
    matched_substring = []

    for word in vocab_list:
        if word.startswith(query):
            matched_prefix.append(word)
            if len(matched_prefix) >= 10:
                return matched_prefix  # Exit early if we have enough prefix matches
        elif query in word:
            matched_substring.append(word)

    # Combine prefix and substring matches, limit to 10 results
    return (matched_prefix + matched_substring)[:10]