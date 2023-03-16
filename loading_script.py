import csv

import requests

INTERNAL_TOOLS_BASE_URL = "https://infx-internal.prod.projectronin.io"

# Load CSV file
# Add new codes to MDA Conditions Terminology V2 (terminology_uuid = d49cabaa-f31c-473c-a059-59b6b7ee2bb7)
# terminology/new_code


def load_from_csv(filename):
    """
    Loads data from the specified CSV file and returns a list of dictionaries
    :param filename: name of the CSV file
    :return: A list of dictionaries
    """
    with open(filename) as input_file:
        csvreader = csv.DictReader(input_file)
        output = []
        for row in csvreader:
            output.append({
                "code": row["display"],
                "display": row["code"],
                "terminology_version_uuid": "d49cabaa-f31c-473c-a059-59b6b7ee2bb7",
                "additional_data": row["additional_data"],
            })
        return output


if __name__ == "__main__":
    new_codes = load_from_csv('mda_condiditions_export_13_mar_2023.csv')
    # print(new_codes[0])
    for new_code in new_codes:
        # Post request to insert new code API
        insert_new_code = requests.post(f'{INTERNAL_TOOLS_BASE_URL}/Terminology/new_code')

# Create a new version of the source value set (value_set_uuid = 'e3d3aa32-d3d7-45be-bbec-624649728560')
#   /ValueSets/e3d3aa32-d3d7-45be-bbec-624649728560/versions/new
#   {
#     "effective_start": "2023-03-15",
#     "effective_end": "2023-03-24",
#     "description": "Add new codes to MDA Conditions Terminology"
#
# Update rules to include the new terminology version and expand the new value set version
#   /ValueSets/e3d3aa32-d3d7-45be-bbec-624649728560/versions/---new_version_uuid_we_created---/update_rules_for_terminology_update
#   json={
#           "old_terminology_version_uuid": "bdeba45e-1b06-4b25-a6ed-cde0469c4978",
#           "new_terminology_version_uuid": "5a5ad7eb-233a-4961-a929-3ae6ef2d7e5b"}

# Data integrity checks
# /ValueSets/diff
#{
#    "previous_version_uuid":"354dd0c5-616d-4b38-a991-5f2cefcbb5bc",
#    "new_version_uuid":"---new_version_uuid_we_created---"
#}

# Publish the new value set version



