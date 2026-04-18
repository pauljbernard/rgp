from __future__ import annotations

from app.models.governance import seed_requests
from app.models.template import seed_templates
from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter


def seed_template_slice(tenant_id: str = "tenant_demo") -> dict[str, int]:
    adapter = DynamoDbGovernancePersistenceAdapter()
    inserted = 0
    skipped = 0

    for template in seed_templates():
        existing = adapter._get_template_item(tenant_id, template.id, template.version)
        if existing is not None:
            skipped += 1
            continue
        adapter._put_template_item(adapter._template_record_to_item(template, tenant_id))
        adapter._refresh_template_current(tenant_id, template.id)
        inserted += 1

    return {
        "inserted": inserted,
        "skipped_existing": skipped,
    }


def seed_request_slice(tenant_id: str = "tenant_demo") -> dict[str, int]:
    adapter = DynamoDbGovernancePersistenceAdapter()
    inserted = 0
    skipped = 0

    for request in seed_requests():
        record = request.model_copy(update={"tenant_id": tenant_id})
        existing = adapter._get_request_item(tenant_id, record.id)
        if existing is not None:
            skipped += 1
            continue
        adapter._put_request_item(adapter._request_record_to_item(record))
        inserted += 1

    return {
        "inserted": inserted,
        "skipped_existing": skipped,
    }


if __name__ == "__main__":
    result = {
        "templates": seed_template_slice(),
        "requests": seed_request_slice(),
    }
    print(result)
