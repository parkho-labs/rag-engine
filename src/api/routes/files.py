from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List
from api.api_constants import *
from models.api_models import ApiResponse, ApiResponseWithBody, FileUploadResponse
from services.unified_file_service import unified_file_service

router = APIRouter()

@router.post(FILES_BASE)
def upload_file(file: UploadFile = File(...), user_id: str = Query(...)) -> FileUploadResponse:
    return unified_file_service.upload_file(file, user_id)

@router.get(FILES_BASE)
def list_files(user_id: str = Query(...)) -> ApiResponseWithBody:
    files = unified_file_service.list_files(user_id)
    return ApiResponseWithBody(
        status="SUCCESS",
        message="Files retrieved successfully",
        body={"files": files}
    )

@router.get(FILES_BASE + "/{file_id}")
def get_file(file_id: str, user_id: str = Query(...)) -> ApiResponse:
    if unified_file_service.file_exists(file_id, user_id):
        return ApiResponse(status="SUCCESS", message=f"File '{file_id}' retrieved successfully")
    else:
        return ApiResponse(status="FAILURE", message="File not found")

@router.delete(FILES_BASE + "/{file_id}")
def delete_file(file_id: str, user_id: str = Query(...)) -> ApiResponse:
    success = unified_file_service.delete_file(file_id, user_id)
    if success:
        return ApiResponse(status="SUCCESS", message=f"File '{file_id}' deleted successfully")
    else:
        return ApiResponse(status="FAILURE", message="File not found or could not be deleted")