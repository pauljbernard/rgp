from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.persistence.dynamodb_seed import seed_request_slice, seed_template_slice


def _dynamodb_resource() -> Any:
    import boto3

    return boto3.resource(
        "dynamodb",
        region_name=settings.dynamodb_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )


def ensure_governance_table(table_name: str | None = None) -> str:
    table_name = table_name or settings.dynamodb_governance_table
    dynamodb = _dynamodb_resource()
    client = dynamodb.meta.client

    try:
        client.describe_table(TableName=table_name)
        return table_name
    except client.exceptions.ResourceNotFoundException:
        pass

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except client.exceptions.ResourceInUseException:
        return table_name
    table.wait_until_exists()
    return table_name


def initialize_template_slice(tenant_id: str = "tenant_demo", *, seed: bool = True) -> dict[str, int | str]:
    table_name = ensure_governance_table()
    seeded = {"inserted": 0, "skipped_existing": 0}
    if seed:
        seeded = seed_template_slice(tenant_id=tenant_id)
    return {
        "table_name": table_name,
        "inserted": seeded["inserted"],
        "skipped_existing": seeded["skipped_existing"],
    }


def initialize_request_slice(tenant_id: str = "tenant_demo", *, seed: bool = True) -> dict[str, int | str]:
    table_name = ensure_governance_table()
    seeded = {"inserted": 0, "skipped_existing": 0}
    if seed:
        seeded = seed_request_slice(tenant_id=tenant_id)
    return {
        "table_name": table_name,
        "inserted": seeded["inserted"],
        "skipped_existing": seeded["skipped_existing"],
    }


if __name__ == "__main__":
    print(
        {
            "templates": initialize_template_slice(),
            "requests": initialize_request_slice(),
        }
    )
