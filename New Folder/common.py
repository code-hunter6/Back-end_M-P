from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """
    Base schema that serializes snake_case Python fields as camelCase JSON
    (stock_count -> stockCount), which is exactly what the React frontend's
    mock data already expects. Inputs accept either spelling.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
