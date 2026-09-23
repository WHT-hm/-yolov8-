from fastapi import APIRouter

from .. import mock_data
from ..schemas import MetaOptions

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/pest-types", response_model=MetaOptions)
def get_meta_options():
    return MetaOptions(
        pest_types=mock_data.PEST_TYPES,
        crop_types=mock_data.CROP_TYPES,
        severity_levels=mock_data.SEVERITY_LEVELS,
    )
