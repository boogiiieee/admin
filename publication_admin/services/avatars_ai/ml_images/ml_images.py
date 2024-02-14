from uuid import uuid4

from publication_admin.services.avatars_ai.service import Service

from .dto import (
    GETInitPersonaTaskResponse,
    GETTextToPictureResponse,
    POSTInitPersonaTaskRequest,
    POSTInitPersonaTaskResponse,
    POSTTextToPictureResponse,
    POSTTextToPictureTaskRequest,
    TaskStatus,
)


class MLImages(Service):
    async def post_init_persona_task(self, *, lora_name: str, s3_paths: list[str]) -> POSTInitPersonaTaskResponse:
        job_id = str(uuid4())
        blog_name = str(uuid4())
        data = await self._make_post_request(
            "/initpersona/task",
            dto_in=POSTInitPersonaTaskRequest(
                lora_name=lora_name, s3_paths=s3_paths, job_id=job_id, blog_name=blog_name
            ),
        )
        return POSTInitPersonaTaskResponse(**data)

    async def get_init_persona_task(self, task_id: str) -> GETInitPersonaTaskResponse:
        data = await self._make_get_request("/initpersona/task", query_params={"task_id": task_id})
        return GETInitPersonaTaskResponse(
            task_id=data["task_id"],
            status=data["status"],
            lora_s3_path=data["data"]["s3_artifact_paths"][0] if data["status"] == TaskStatus.SUCCESS else None,
        )

    async def create_text_to_picture_task(
        self, *, lora_name: str, lora_s3_path: str, caption: str, blog_name: str = ""
    ) -> POSTTextToPictureResponse:
        job_id = str(uuid4())
        data = await self._make_post_request(
            "/t2p-lora/task",
            dto_in=POSTTextToPictureTaskRequest(
                lora_name=lora_name,
                lora_s3_path=lora_s3_path,
                caption=caption,
                blog_name=blog_name,
                job_id=job_id,
                filename=f"{job_id}.jpeg",
            ),
        )
        return POSTTextToPictureResponse(**data)

    async def get_text_to_picture_task(self, task_id: str) -> GETTextToPictureResponse:
        data = await self._make_get_request("/t2p-lora/task", query_params={"task_id": task_id})
        return GETTextToPictureResponse(
            task_id=data["task_id"],
            status=data["status"],
            image_path=data["data"]["s3_paths"][0] if data["status"] == TaskStatus.SUCCESS else None,
        )
