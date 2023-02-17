import requests
import json

SNOWSTORM_BASE_URL = "https://snowstorm.prod.projectronin.io/MAIN"

def filter_non_snomed_codes(coding_array):
    """

    Parameters:
    coding_array (list of dict): A list of coding objects that contain information about clinical codes and their associated systems.

    Returns:
    filtered_array (list of dict): A list of SNOMED CT codes and their associated text, extracted from the input coding_array.
    If no SNOMED CT codes are found in the input coding_array, returns None.
    """
    filtered_array = []
    for coding in coding_array:
        if coding['system'] in ['http://snomed.info/sct', 'urn:oid:2.16.840.1.113883.6.96']:
            filtered_array.append(coding['code'])
    return filtered_array



def get_preferred_term_and_fully_specified_name(filtered_array):
    """
    Check if an incoming coding object is suitable for automatic mapping to a standardized concept in SNOMED CT, by searching
    for an exact match between the incoming text and the preferred term or fully-specified name of the corresponding SNOMED CT
    concept. If no exact match is found, returns False and adds the SNOMED CT code to a synonym_check_array for synonym matching.

    Parameters:
    filtered_array (dict): A dictionary containing an array of coding objects and a text string.

    Returns:
    If a match is found and the mapping is successful, returns True.
    If no match is found, returns False and appends the SNOMED CT code to synonym_check_array.
    If the input coding array does not contain any SNOMED CT codes, returns None.
    """
    sctid = filtered_array[0]
    pt_fsn_search = requests.get(
        f"{SNOWSTORM_BASE_URL}/concepts?conceptIds={sctid}",
    ).json()
    if pt_fsn_search == {"error": "NOT_FOUND", "message": "Concept not found"}:
        return None
    else:
        first_item = pt_fsn_search["items"][0]
        pt = first_item["pt"]["term"]
        fsn = first_item["fsn"]["term"]
        return fsn,pt


def get_synonyms(filtered_array):
    """


    Parameters:
    synonym_check_array (dict):

    Returns:

    """
    us_en = "900000000000509007"
    synonym_status = ["ACCEPTABLE", "PREFERRED"]
    syn_search = requests.get(f"{SNOWSTORM_BASE_URL}/concepts/{filtered_array[0]}/descriptions").json()
    syn_list = []
    for item in syn_search["conceptDescriptions"]:
        if item["type"] == "SYNONYM":
            if us_en in item["acceptabilityMap"]:
                if item["acceptabilityMap"][us_en] in synonym_status:
                    syn_list.append(item["term"])
    return syn_list

def check_match(client_display_text,list_of_names):
        if client_display_text in list_of_names:
            return True
        else:
            return False

def auto_map(filtered_array):
    #  call to add new item into terminology
    #  does relevant concept map has version currently in draft
    #  if yes, add to map --> 1.create source concept 2.create mapping
    # if no, create a new version in draft and add the concept
    pass

def manual_map(filtered_array):
    # does relevant concept map has version currently in draft
    # if yes, add to map --> 1.create source concept 2.create mapping
    # if no, create a new version in draft and add the concept
    pass


if __name__ == "__main__":
    # load unresolved errors from the error service
    # But for now, load from file
    with open('sample_data.json') as json_input:
        sample_data = json.load(json_input)
    for condition in sample_data:
        coding_array = condition["coding"]
        client_display_text = condition["text"]
        filtered_array = filter_non_snomed_codes(coding_array)

        if len(filtered_array) > 1:
            manual_map(filtered_array)
        can_automap = False
        fully_specified_name, preferred_term = get_preferred_term_and_fully_specified_name(filtered_array)
        if check_match(client_display_text, [fully_specified_name, preferred_term]):
             can_automap = True
        else:
            acceptable_and_preferred_synonyms = get_synonyms(filtered_array)
            if check_match(client_display_text, acceptable_and_preferred_synonyms):
                can_automap = True
        if can_automap is True:
            auto_map(filtered_array)
        else:
            manual_map(filtered_array)
