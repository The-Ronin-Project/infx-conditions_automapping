def get_snomed_terms(input_data):
    """
    Returns the SNOMED terms that match the input text by searching the SNOMED terminology.
    @param input_data: the input data to be matched
    @return: a list of SNOMED terms that match the input text
    """
    coding_array = input_data["coding"]
    snomed_terms = []
    for coding in coding_array:
        if coding["system"] in ["http://snomed.info/sct", "urn:oid:2.16.840.1.113883.6.96"]:
            sctid = coding["code"]
            pt_search = requests.get(
                f"{SNOWSTORM_BASE_URL}/concepts?conceptIds={sctid}",
            ).json()
            if pt_search == {"error": "NOT_FOUND", "message": "Concept not found"}:
                # TODO log error and sent the row to manual mapping
                return None
            else:
                first_item = pt_search["items"][0]
                pt = first_item["pt"]["term"]
                fsn = first_item["fsn"]["term"]
                if input_data["text"] in [pt,fsn]:
                    snomed_terms.append(pt)
                    snomed_terms.append(fsn)
                else:
                    syn_search = requests.get(
                        f"{SNOWSTORM_BASE_URL}/concepts/{sctid}/descriptions",
                    ).json()
                    concept_description = syn_search["conceptDescriptions"]
                    for item in concept_description:
                        syn_list = []
                        if item["type"] == "SYNONYM":
                            if "900000000000509007" in item["acceptabilityMap"]:
                                if item["acceptabilityMap"]["900000000000509007"] in ["ACCEPTABLE", "PREFERRED"]:
                                    syn_list.append(item["term"])
                                    if input_data["text"] in syn_list:
                                        snomed_terms.append(item["term"])
    return snomed_terms

def process_system_snomed_for_term_match(input_data):
    """
    Confirms concept is suitable for automapping by checking snowstorm for exact match of incoming {'coding':'text'}
    with SNOMED pt, fsn, preferred synonym, or acceptable synonym.
    @param input_data: the input data to be matched
    @return:
    """
    snomed_terms = get_snomed_terms(input_data)
    if snomed_terms:
        print(f'Match found for: {input_data["text"]}')
        #  call to add new item into terminology
        #  does relevant concept map have version currently in draft
        #  if yes add to map --> 1.create source concept 2.create mapping
        # if no create a new version in draft and add the concept
    else:
        print(f'No match found for: {input_data["text"]}')
        # TODO log error and sent the row to manual mapping
    return
