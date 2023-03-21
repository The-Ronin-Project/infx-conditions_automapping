import requests
import re
from sqlalchemy import create_engine, text
from decouple import config

# Replace with your API base URL and access credentials (if required)
API_BASE_URL = "https://snowstorm.prod.projectronin.io"
# API_ACCESS_KEY = "your_api_access_key"

SYNONYMS = {
    "tumor": "neoplasm",
    "secondary": "metastatic",
}

def get_concepts_to_automap():
    """
        Retrieves a list of unmapped concepts from the database, parses their displays
        into coding arrays, and identifies concepts with exactly one SNOMED code.

        This function connects to a PostgreSQL database, retrieves a list of unmapped
        concepts for a specific project identified by a UUID. It then parses the display of each concept into a
        coding array and checks if there is exactly one SNOMED code within the coding
        array. If so, the SNOMED code and the display are added to the final list of
        automapping candidates.

        Returns:
            list: A list of dictionaries containing the SNOMED code and display for
            each concept with exactly one SNOMED code. The list may be empty if no
            such concepts are found.

        Database connection:
            This function uses the `create_engine` function from the SQLAlchemy library
            to connect to a PostgreSQL database. It reads the database credentials
            (user, password, host, and name) from environment variables.

        Example:
            automap_candidates = get_concepts_to_automap()
            print(automap_candidates)
        """

    # Connect to database and retrieve unmapped concepts for this project
    engine = create_engine(
        f"postgresql://{config('DATABASE_USER')}@{config('DATABASE_HOST')}:{config('DATABASE_PASSWORD')}@{config('DATABASE_HOST')}/{config('DATABASE_NAME')}",
        connect_args={'sslmode': 'require'})
    conn = engine.connect()

    data_to_map = conn.execute(
        text(
            """
            SELECT *
            FROM concept_maps.source_concept sc
            WHERE sc.concept_map_version_uuid = '2591b35f-b248-45f7-a2a0-d9e05d106fb6'
            AND NOT EXISTS (
                SELECT 1
                FROM concept_maps.concept_relationship cr
                WHERE cr.source_concept_uuid = sc.uuid
            )
            limit 500
            """
        )
    )

    final_automapping_candidates = []

    # Parse their displays into coding arrays
    for item in data_to_map:
        input_display = item.code
        input_coding_array = item.display
        source_concept_uuid = item.uuid

        # Remove the outer curly braces
        input_str = input_coding_array[1:-1]

        # Find the tuples using a regular expression
        tuple_pattern = r'\{([^}]+)\}'
        tuple_matches = re.findall(tuple_pattern, input_str)

        # Convert each matched tuple into a dictionary
        coding_array = []
        for match in tuple_matches:
            items = match.split(', ')
            d = {
                "code": items[0],
                "display": items[1],
                "system": items[2],
            }
            coding_array.append(d)

        # Identify coding arrays with exactly one SNOMED code
        count = 0
        snomed_code = None
        for obj in coding_array:
            if obj['system'] == 'http://snomed.info/sct' or obj['system'] == 'urn:oid:2.16.840.1.113883.6.96':
                count += 1
                snomed_code = obj['code']

        if count == 1:
            final_automapping_candidates.append(
                {
                    'code': snomed_code,
                    'display': input_display,
                    'source_concept_uuid': source_concept_uuid
                }
            )
        else:
            # print("Will not attempt automapping", input_display, input_coding_array)
            pass

    # Return final list of items to auto-map
    return final_automapping_candidates

def normalize_synonyms(text):
    words = text.split()
    normalized_words = [SYNONYMS.get(word.lower(), word) for word in words]
    return " ".join(normalized_words)

def get_concept_data(concept_id, branch="MAIN/2023-03-01"):
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

def get_concept_descriptions(concept_id, branch="MAIN/2023-03-01"):
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

def do_mapping(source_concept_uuid, code, display, matched_reason):
    # Assign mapping row to Automapping user
    # todo: implement this

    # Submit mapping

    requests.post(
        'https://infx-internal.prod.projectronin.io/mappings/',
        json={
            "source_concept_uuid": source_concept_uuid,
            "relationship_code_uuid": "f2a20235-bd9d-4f6a-8e78-b3f41f97d07f",
            "target_concept_code": code,
            "target_concept_display": display,
            "target_concept_terminology_version_uuid": "306ae926-50aa-41d1-8ec8-1df123b0cd77",
            "mapping_comments": f"{matched_reason} match",
            "author": "Automapping"
        }
    )
    print("Mapped:", code, '|', display, matched_reason, 'to source concept:', source_concept_uuid)

def main():
    # input_codes = [
    #     {"code": "386661006", "display": "Fever", "expected_matched_reason": "EXACT"},
    #     {"code": "422587007", "display": "Nausea", "expected_matched_reason": "EXACT"},
    #     {"code": "386661006", "display": "Pyrexia", "expected_matched_reason": "SYNONYM"},
    #     {"code": "94579000", "display": "Secondary malignant neoplasm of skin", "expected_matched_reason": "EXACT"},
    #     {"code": "94579000", "display": "Secondary cancer of skin", "expected_matched_reason": "SYNONYM"},
    #     {"code": "267036007", "display": "Shortness of breath", "expected_matched_reason": "SYNONYM"},
    #     {"code": "399068003", "display": "Malignant tumor of prostate", "expected_matched_reason": "EXACT"},
    #     {"code": "126926005", "display": "Neoplasm of breast (disorder)", "expected_matched_reason": "EXACT"},
    #     {"code": "187725002", "display": "Malignant neoplasm of upper third of esophagus", "expected_matched_reason": "SYNONYM"},
    #     {"code": "94602001", "display": "Secondary malignant neoplasm of vertebral column", "expected_matched_reason": "EXACT"},
    #     {"code": "792907004", "display": "Adenocarcinoma, NOS of pancreatic duct", "expected_matched_reason": "NORMALIZED DESCRIPTION"},
    #     {"code": "705176003", "display": "Secondary carcinoid tumor", "expected_matched_reason": "SYNONYM"},
    #     {"code": "34713006", "display": "Vitamin D deficiency, not otherwise specified",
    #      "expected_matched_reason": "NORMALIZED DESCRIPTION"},
    #     {"code": "340491000119104", "display": "Hordeolum externum of left eyelid, not otherwise specified", "expected_matched_reason": "NORMALIZED DESCRIPTION"},
    #     {"code": "353511000119101", "display": "Primary malignant neoplasm of female right breast, not otherwise specified", "expected_matched_reason": "NORMALIZED DESCRIPTION"},
    # ]
    input_codes = get_concepts_to_automap()

    ignorable_strings = [", NOS", ", not otherwise specified"]

    for item in input_codes:
        code = item["code"]
        input_display = item["display"]
        preferred_term, fully_specified_name, is_active = get_concept_data(code)
        if (preferred_term, fully_specified_name, is_active) == (None, None, None):
            continue
        concept_descriptions = get_concept_descriptions(code)
        if not concept_descriptions:
            continue

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

        if is_active:
            if matched_code:
                print(matched_reason, "MATCH", input_display, code, fsn_for_matched_code)
                do_mapping(item.get('source_concept_uuid'), matched_code, fsn_for_matched_code, matched_reason)
            else:
                print("NO MATCH", input_display)
            # if matched_reason != item.get('expected_matched_reason'):
            #     print("--------- UNEXPECTED RESULT -----------")


if __name__ == "__main__":
    main()
