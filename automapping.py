import requests

# Replace with your API base URL and access credentials (if required)
API_BASE_URL = "https://snowstorm.prod.projectronin.io"
# API_ACCESS_KEY = "your_api_access_key"

SYNONYMS = {
    "tumor": "neoplasm",
    "secondary": "metastatic",
}

def normalize_synonyms(text):
    words = text.split()
    normalized_words = [SYNONYMS.get(word.lower(), word) for word in words]
    return " ".join(normalized_words)

def get_concept_data(concept_id, branch="MAIN"):
    """
    Fetches the preferred term, fully specified name, and status for the given concept ID
    using the SNOMED API.

    Args:
        concept_id (str): The SNOMED concept ID to fetch data for.
        branch (str): The branch of the concepts repository (default: "MAIN").

    Returns:
        tuple: A tuple containing the preferred term, fully specified name, and status of the concept.
    """
    url = f"{API_BASE_URL}/{branch}/concepts/{concept_id}"
    response = requests.get(url)

    if response.status_code == 200:
        concept_data = response.json()
        preferred_term = concept_data["pt"]["term"]
        fully_specified_name = concept_data["fsn"]["term"]
        is_active = concept_data["active"]
        return preferred_term, fully_specified_name, is_active
    else:
        print(f"Error fetching data for concept ID {concept_id}: {response.status_code}")
        return None, None, None

def get_concept_descriptions(concept_id, branch="MAIN"):
    """
    Fetches the descriptions for the given concept ID using the SNOMED API.

    Args:
        concept_id (str): The SNOMED concept ID to fetch descriptions for.
        branch (str): The branch of the concepts repository (default: "MAIN").

    Returns:
        list: A list of description terms for the given concept ID.
    """
    url = f"{API_BASE_URL}/{branch}/concepts/{concept_id}/descriptions"
    headers = {
        "Accept-Language": "en-X-900000000000509007"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        descriptions_data = response.json()
        descriptions = descriptions_data["conceptDescriptions"]
        filtered_terms = [
            desc['term'] for desc in descriptions
            if any(value in {"ACCEPTABLE", "PREFERRED"} for value in desc["acceptabilityMap"].values())
        ]
        return filtered_terms
    else:
        print(f"Error fetching descriptions for concept ID {concept_id}: {response.status_code}")
        return None


def main():
    input_codes = [
        {"code": "386661006", "display": "Fever", "expected_matched_reason": "EXACT"},
        {"code": "422587007", "display": "Nausea", "expected_matched_reason": "EXACT"},
        {"code": "386661006", "display": "Pyrexia", "expected_matched_reason": "SYNONYM"},
        {"code": "94579000", "display": "Secondary malignant neoplasm of skin", "expected_matched_reason": "EXACT"},
        {"code": "94579000", "display": "Secondary cancer of skin", "expected_matched_reason": "SYNONYM"},
        {"code": "267036007", "display": "Shortness of breath", "expected_matched_reason": "SYNONYM"},
        {"code": "399068003", "display": "Malignant tumor of prostate", "expected_matched_reason": "EXACT"},
        {"code": "126926005", "display": "Neoplasm of breast (disorder)", "expected_matched_reason": "EXACT"},
        {"code": "187725002", "display": "Malignant neoplasm of upper third of esophagus", "expected_matched_reason": "SYNONYM"},
        {"code": "94602001", "display": "Secondary malignant neoplasm of vertebral column", "expected_matched_reason": "EXACT"},
        {"code": "792907004", "display": "Adenocarcinoma, NOS of pancreatic duct", "expected_matched_reason": "NORMALIZED DESCRIPTION"},
        {"code": "705176003", "display": "Secondary carcinoid tumor", "expected_matched_reason": "SYNONYM"},
        {"code": "34713006", "display": "Vitamin D deficiency, not otherwise specified",
         "expected_matched_reason": "NORMALIZED DESCRIPTION"},
        {"code": "340491000119104", "display": "Hordeolum externum of left eyelid, not otherwise specified", "expected_matched_reason": "NORMALIZED DESCRIPTION"},
        {"code": "353511000119101", "display": "Primary malignant neoplasm of female right breast, not otherwise specified", "expected_matched_reason": "NORMALIZED DESCRIPTION"},
        
    ]

    ignorable_strings = [", NOS", ", not otherwise specified"]

    for item in input_codes:
        code = item["code"]
        input_display = item["display"]
        preferred_term, fully_specified_name, is_active = get_concept_data(code)
        concept_descriptions = get_concept_descriptions(code)

        matched_code = None
        fsn_for_matched_code = None
        matched_reason = None

        if input_display == preferred_term or input_display == fully_specified_name:
            matched_code = code
            fsn_for_matched_code = get_concept_data(matched_code)[1]
            matched_reason = "EXACT"
        else:
            normalized_input_display = normalize_synonyms(input_display)
            descriptions_to_check = [preferred_term, fully_specified_name] + concept_descriptions

            if any(normalized_input_display == description for description in descriptions_to_check):
                matched_code = code
                fsn_for_matched_code = get_concept_data(matched_code)[1]
                matched_reason = "SYNONYM"
            else:
                modified_display = normalized_input_display
                for string in ignorable_strings:
                    modified_display = modified_display.replace(string, '')

                if any(modified_display == description for description in descriptions_to_check):
                    matched_code = code
                    fsn_for_matched_code = get_concept_data(matched_code)[1]
                    matched_reason = "NORMALIZED DESCRIPTION"
                else:
                    print("NO MATCH", input_display)

        if not is_active:
            pass
            # Lookup an appropriate substitute
            # set matched_code to be the substitute
            # Matched reason: ACTIVE SUBSTITUTE

        if matched_code:
            print(matched_reason, "MATCH", input_display, code, fsn_for_matched_code)
        else:
            print("NO MATCH", input_display)
        if matched_reason != item.get('expected_matched_reason'):
            print("--------- UNEXPECTED RESULT -----------")


if __name__ == "__main__":
    main()
