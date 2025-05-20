import re

def clean_query(query):
    query = query.lower()
    query = re.sub(r"^(what is|who is|define|explain|tell me about)\s+", "", query)
    return query.strip().capitalize()
