from app.models.template import TemplateRecord, seed_templates


class InMemoryTemplateRepository:
    def __init__(self) -> None:
        self._items = seed_templates()

    def list(self) -> list[TemplateRecord]:
        return self._items


template_repository = InMemoryTemplateRepository()
