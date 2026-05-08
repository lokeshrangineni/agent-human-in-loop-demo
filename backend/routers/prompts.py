from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.models.schemas import UserInfo
from backend.routers.auth import get_current_user
from backend.services.prompt_manager import (
    get_all_prompts_summary,
    get_prompt_history,
    get_active_prompt,
    create_prompt_version,
    activate_prompt_version,
)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptUpdateRequest(BaseModel):
    content: str
    change_summary: str


class PromptActivateRequest(BaseModel):
    version_id: str


@router.get("")
async def list_prompts(user: UserInfo = Depends(get_current_user)):
    """List all prompt keys with their active version summary. Admin only."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view prompts")
    return get_all_prompts_summary()


@router.get("/{prompt_key}")
async def get_prompt(
    prompt_key: str,
    user: UserInfo = Depends(get_current_user),
):
    """Get the active prompt content and full version history. Admin only."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view prompt details")

    history = get_prompt_history(prompt_key)
    if not history:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_key}' not found")

    active_content = get_active_prompt(prompt_key)
    active_version = next((v for v in history if v["is_active"]), None)

    return {
        "prompt_key": prompt_key,
        "active_content": active_content,
        "active_version": active_version,
        "versions": history,
    }


@router.post("/{prompt_key}")
async def update_prompt(
    prompt_key: str,
    req: PromptUpdateRequest,
    user: UserInfo = Depends(get_current_user),
):
    """Create a new version of a prompt and activate it. Admin only."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update prompts")

    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Prompt content cannot be empty")

    if not req.change_summary.strip():
        raise HTTPException(status_code=400, detail="Change summary is required")

    try:
        version = create_prompt_version(
            prompt_key=prompt_key,
            content=req.content,
            change_summary=req.change_summary,
            created_by=user.id,
            activate=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return version


@router.post("/{prompt_key}/activate")
async def revert_prompt(
    prompt_key: str,
    req: PromptActivateRequest,
    user: UserInfo = Depends(get_current_user),
):
    """Activate a specific version of a prompt (revert). Admin only."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can revert prompts")

    try:
        version = activate_prompt_version(prompt_key, req.version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return version
