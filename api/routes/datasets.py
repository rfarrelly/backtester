from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from app.application.dataset_service import DatasetService
from app.infrastructure.db.session import get_db
from app.infrastructure.persistence_models.user import User

router = APIRouter(prefix="/datasets", tags=["datasets"])


MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25MB MVP guardrail


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv uploads are supported")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    service = DatasetService(db)
    ds = service.save_upload(
        owner_user_id=current_user.id,
        filename=file.filename,
        file_bytes=content,
    )

    return {
        "dataset_id": str(ds.id),
        "filename": ds.original_filename,
    }


@router.get("/{dataset_id}/introspect")
def introspect_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DatasetService(db)

    try:
        ds = service.get_owned_dataset(
            dataset_id=dataset_id, owner_user_id=current_user.id
        )
        info = service.introspect(dataset=ds, sample_size=25)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "dataset_id": str(ds.id),
        "filename": ds.original_filename,
        "columns": info.columns,
        "inferred_types": info.inferred_types,
        "sample_rows": info.sample_rows,
    }
