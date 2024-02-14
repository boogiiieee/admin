from enum import StrEnum

from pydantic import BaseModel


class TaskStatus(StrEnum):
    SUCCESS: str = "SUCCESS"
    PENDING: str = "PENDING"
    STARTED: str = "STARTED"
    FAILURE: str = "FAILURE"

    def is_success(self) -> bool:
        return self == self.SUCCESS


class POSTInitPersonaTaskRequest(BaseModel):
    lora_name: str
    s3_paths: list[str]
    job_id: str
    blog_name: str


class POSTInitPersonaTaskResponse(BaseModel):
    task_id: str
    status: str


class GETInitPersonaTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    lora_s3_path: str | None


class POSTTextToPictureTaskRequest(BaseModel):
    lora_name: str
    lora_s3_path: str
    caption: str
    blog_name: str
    job_id: str
    filename: str
    num_samples: int = 1


class POSTTextToPictureResponse(BaseModel):
    task_id: str
    status: str


class GETTextToPictureResponse(BaseModel):
    task_id: str
    status: TaskStatus
    image_path: str | None
