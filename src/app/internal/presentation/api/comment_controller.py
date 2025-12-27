from fastapi import APIRouter, Depends, HTTPException, status
from src.app.internal.domain.services.get_queue_comments import GetQueueCommentsUseCase
from src.app.internal.domain.services.upsert_comment import UpsertCommentUseCase
from src.app.internal.presentation.scheme.comment_schema import UpsertCommentRequest, CommentResponse
from .dependencies import *
from .auth_controller import get_current_user


router = APIRouter(prefix="/comments", tags=["comments"])

@router.get("/queue/{queue_id}", response_model=list[CommentResponse])
async def get_queue_comments(
    queue_id: str,
    current_user=Depends(get_current_user),
    comment_repo=Depends(get_comment_repository),
    queue_repo=Depends(get_queue_repository),
):
    """
        Возвращает 5 последних комментариев пользователя
    """
    use_case = GetQueueCommentsUseCase(queue_repo, comment_repo)

    try:
        return await use_case.execute(
            user_id=current_user.uuid,
            queue_id=queue_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("", status_code=status.HTTP_200_OK)
async def upsert_comment(
    data: UpsertCommentRequest,
    current_user=Depends(get_current_user),
    comment_repo=Depends(get_comment_repository),
    record_repo=Depends(get_record_repository),
    queue_repo=Depends(get_queue_repository)
):
    """
        Добавление комментария Владельца очереди к заявке.
        Если передано только record_id и text, то считается, что комментарий новый.
        Если добавлено comment_id с id одного из 5 последних комментариев, то программа не будет
        обновлять список последних комментариев, только изменит последнюю дату использования переданного комментария
    """
    use_case = UpsertCommentUseCase(
        record_repo=record_repo,
        comment_repo=comment_repo,
        queue_repo=queue_repo
    )

    try:
        await use_case.execute(
            record_id=data.record_id,
            text=data.text,
            comment_id=data.comment_id,
            user_id=current_user.uuid
        )
        return {"msg": "ok"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )