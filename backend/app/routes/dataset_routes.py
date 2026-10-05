from fastapi import APIRouter, File, UploadFile, HTTPException, status
from backend.app.schemas.dataset_schema import DatasetUploadResponse
from backend.app.services.ingestion import (
    parse_and_validate_csv_content,
    load_preset_pilot_dataset,
)

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload custom CSV dataset",
    description="Uploads a CSV file containing user retrieval observations, validates schema and URLs, and saves the raw dataset."
)
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are accepted for dataset upload."
        )
    
    try:
        content_bytes = await file.read()
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content must be valid UTF-8 encoded CSV text."
        )
    
    try:
        response = parse_and_validate_csv_content(content_str)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during CSV processing: {str(e)}"
        )


@router.get(
    "/preset",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Load preset pilot dataset",
    description="Loads pre-bundled sample dataset (12 public user observations) for 1-click reviewer testing."
)
async def get_preset_dataset():
    try:
        response = load_preset_pilot_dataset()
        return response
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load preset pilot dataset: {str(e)}"
        )
