"""Compliance check example"""

from verifai_sdk import VerifAIClient
from verifai_sdk.models import ComplianceFramework


def run_compliance_check():
    client = VerifAIClient(api_key="your-api-key")

    result = client.check_compliance(
        "We store user emails and IP addresses.",
        framework=ComplianceFramework.GDPR,
    )

    print(f"Compliance score: {result.score:.2f}")
    print(f"Risk level: {result.risk_level}")

    if result.violations:
        for violation in result.violations:
            print(f"  - {violation.description}")

    client.close()


if __name__ == "__main__":
    run_compliance_check()
