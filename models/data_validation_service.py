import json
from decouple import config
from dataclasses import dataclass, field

from requests.exceptions import HTTPError
import requests

def get_access_token():
    base_url = config("auth0_url")
    payload = {
        "grant_type": "client_credentials",
        "client_id": config("auth0_client_id"),
        "client_secret": config("auth0_client_secret"),
        "audience": config("auth0_audience"),
    }
    response = requests.post(base_url, data=payload)
    return response.json()["access_token"]


@dataclass
class Resource:
    id: str
    resource_type: str
    resource: str
    status: str
    severity: str
    issues: list = field(default_factory=list)

    @property
    def code_error_issues(self):
        return [issue for issue in self.issues if issue.type=="RONIN_NOV_CODING_001"]  # Ronin no valid coding errors only

    def load_issues(self):
        access_token = get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"https://interop-validation.prod.projectronin.io/resources/{self.id}/issues",
            headers=headers,
        )
        issues = response.json()

        for issue in issues:
            self.issues.append(
                Issue(
                    id=issue.get("id"),
                    severity=issue.get('severity'),
                    type=issue.get('type'),
                    description=issue.get('description'),
                    status=issue.get('status')
                )
            )

@dataclass
class Issue:
    id: str
    severity: str
    type: str
    description: str
    status: str


def get_resources_from_service():
    """
    This will be the first part of the infx error ingestion. Getting the errors.
    @return:
    """
    # get token
    access_token = get_access_token()
    # Add the token to the Authorization header of the request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    # Get resources using the token
    data_validation_resources = requests.get(
        "https://interop-validation.prod.projectronin.io/resources",
        # this end point has parameters to filter by status, organization_id and/or resource_type
        headers=headers,
    ).json()
    return [
        Resource(
            id=item.get('id'),
            resource_type=item.get('resource_type'),
            resource=item.get('resource'),
            status=item.get('status'),
            severity=item.get('severity')
        ) for item in data_validation_resources
    ]


if __name__ == "__main__":
    # resources = get_resources_from_service()
    resources = [
        Resource(
            id="3ee69f7a-8d6c-4051-ba6f-7bfec6877d9c",
            resource_type="Condition",
            resource={
                "resourceType": "Condition",
                "clinicalStatus": "active",
                "code": [
                    {
                        "coding": [
                            {
                                "code": "274533004",
                                "display": "Abnormal findings on diagnostic imaging of lung (finding)",
                                "system": "http://snomed.info/sct"
                            },
                            {
                                "code": "793.19",
                                "display": "Abnormal findings on diagnostic imaging of lung",
                                "system": "http://hl7.org/fhir/sid/icd-9-cm/diagnosis"
                            },
                            {
                                "code": "R91.8",
                                "display": "Abnormal findings on diagnostic imaging of lung",
                                "system": "urn:oid:2.16.840.1.113883.6.90"
                            }
                        ]
                    }
                ],
                "text": "Abnormal findings on diagnostic imaging of lung"
            },
            status="REPORTED",
            severity="FAILED",
            issues=[
                Issue(
                    id="9ce8e75e-ec11-4620-ba20-c2ad42c623cb",
                    severity="FAILED",
                    type="RONIN_NOV_ID_001",
                    description="FHIR identifier is required",
                    status="REPORTED"
                )
            ]
        )
    ]
    for resource in resources:
        # if resource.severity != 'failed':
        #     continue

        # resource.load_issues()
        if len(resource.issues) > 0:
            print(resource)
            for issue in resource.issues:
                print(issue)

