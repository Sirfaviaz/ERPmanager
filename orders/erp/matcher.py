from fuzzywuzzy import fuzz

def get_top_matches(extracted_name, items, top_n=3, threshold=30):  # lowered threshold
    matches = []

    for item in items:
        score = fuzz.token_sort_ratio(extracted_name.lower(), item['item_name'].lower())
        matches.append({
            "item_code": item['item_code'],
            "item_name": item['item_name'],
            "score": score
        })

    sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)
    return [m for m in sorted_matches[:top_n] if m["score"] >= threshold]
