"""
SATELLITE PRO - SNS APIルーター
MongoDB Atlas のコメントCRUDをFastAPIエンドポイントとして公開

エンドポイント:
  GET  /api/sns/comments?farm_id=hokkaido       農地のコメント取得
  POST /api/sns/comments                         コメント投稿
  POST /api/sns/comments/{id}/like              いいね
  DELETE /api/sns/comments/{id}?user_id=xxx     削除
  GET  /api/sns/feed                            全農地の最新フィード
  GET  /api/sns/health                          MongoDB接続確認
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from services.mongo import (
    get_comments, create_comment, like_comment,
    delete_comment, get_recent_comments, mongo_health
)

router = APIRouter(prefix="/api/sns", tags=["SNS"])

# =============================================
# リクエスト/レスポンスモデル
# =============================================

class CommentCreateRequest(BaseModel):
    farm_id: str = Field(..., description="農地ID（Supabase farms.id）")
    user_id: str = Field(..., description="ユーザーID（Supabase users.id）")
    user_name: str = Field(..., max_length=50, description="表示名")
    text: str = Field(..., min_length=1, max_length=500, description="コメント本文")
    photo_url: Optional[str] = Field(None, description="添付写真URL（Supabase Storage）")
    tags: list[str] = Field(default_factory=list, description="タグリスト")

class CommentResponse(BaseModel):
    _id: str
    farm_id: str
    user_id: str
    user_name: str
    text: str
    photo_url: Optional[str]
    likes: int
    tags: list[str]
    created_at: str

# =============================================
# エンドポイント
# =============================================

@router.get("/comments")
def list_comments(
    farm_id: str = Query(..., description="農地ID"),
    limit: int = Query(50, ge=1, le=200, description="取得件数"),
    skip: int = Query(0, ge=0, description="スキップ件数（ページネーション）"),
):
    """
    農地IDに紐づくコメント一覧を新しい順で取得

    例: GET /api/sns/comments?farm_id=hokkaido&limit=20
    """
    try:
        comments = get_comments(farm_id=farm_id, limit=limit, skip=skip)
        return {"farm_id": farm_id, "total": len(comments), "comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments", status_code=201)
def post_comment(req: CommentCreateRequest):
    """
    コメントを新規投稿（MongoDB Atlasに保存）

    例:
    POST /api/sns/comments
    {
      "farm_id": "hokkaido",
      "user_id": "uuid-from-supabase",
      "user_name": "田中農園",
      "text": "今年のコシヒカリは生育が早いです！",
      "tags": ["水稲", "生育"]
    }
    """
    # 入力バリデーション
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="コメント本文が空です")
    if len(req.tags) > 5:
        raise HTTPException(status_code=422, detail="タグは5個以内にしてください")

    try:
        comment = create_comment(
            farm_id=req.farm_id,
            user_id=req.user_id,
            user_name=req.user_name,
            text=req.text,
            photo_url=req.photo_url,
            tags=req.tags,
        )
        # datetime を ISO 文字列に変換（JSON化のため）
        if hasattr(comment.get("created_at"), "isoformat"):
            comment["created_at"] = comment["created_at"].isoformat()
            comment["updated_at"] = comment["updated_at"].isoformat()
        return {"success": True, "comment": comment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments/{comment_id}/like")
def add_like(comment_id: str):
    """
    コメントにいいね（+1）

    例: POST /api/sns/comments/66abc123.../like
    """
    try:
        likes = like_comment(comment_id)
        return {"success": True, "likes": likes}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/comments/{comment_id}")
def remove_comment(comment_id: str, user_id: str = Query(..., description="投稿者のユーザーID")):
    """
    コメント削除（投稿者本人のみ）

    例: DELETE /api/sns/comments/66abc123...?user_id=uuid-from-supabase
    """
    try:
        deleted = delete_comment(comment_id=comment_id, user_id=user_id)
        if not deleted:
            raise HTTPException(status_code=403, detail="削除権限がないか、コメントが存在しません")
        return {"success": True, "deleted_id": comment_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feed")
def get_feed(limit: int = Query(20, ge=1, le=100)):
    """
    全農地の最新コメントをタイムライン形式で取得（SNSフィード）

    例: GET /api/sns/feed?limit=30
    """
    try:
        comments = get_recent_comments(limit=limit)
        for c in comments:
            if hasattr(c.get("created_at"), "isoformat"):
                c["created_at"] = c["created_at"].isoformat()
        return {"total": len(comments), "feed": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def sns_health():
    """MongoDB接続ヘルスチェック"""
    result = mongo_health()
    if result.get("status") != "ok":
        raise HTTPException(status_code=503, detail=result.get("error"))
    return result
