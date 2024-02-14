from typing import Any

from pydantic import BaseModel, ConfigDict

from publication_admin.services.avatars_ai.service import Service


class BioData(BaseModel):
    name: str
    topics: str
    text: str


class BioRequest(BaseModel):
    data: BioData
    config: Any = {}


class BioResponse(BaseModel):
    text: str | None

    model_config = ConfigDict(extra="allow")


class MLText(Service):
    async def bio(self, *, name: str, text: str, topics: str) -> BioResponse:
        dto = BioRequest(data=BioData(name=name, text=text, topics=topics))
        data = await self._make_post_request("/bio", dto_in=dto)
        return BioResponse(**data)
