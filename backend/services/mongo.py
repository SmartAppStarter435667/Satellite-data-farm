"""
SATELLITE PRO - MongoDB Atlas 接続・コメントCRUD
SNSコメント機能の永続化レイヤー

使用ライブラリ: pymongo (requirements.txtに追加済み)
接続URI: mongodb+srv://user:pass@cluster.mongodb.net/satellite_pro
"""
import os
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection

# =============================================
# 接続管理（シングルトン）
# =============================================
_client: Optional[MongoClient] = None
_db = None

def get_db():
    """MongoDBクライアントのシングルトン取得"""
    global _client, _db
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI が設定されていません")
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        _db = _client["satellite_pro"]
        # インデックス作成（初回のみ）
        _ensure_indexes(_db)
    return _db

def _ensure_indexes(db):
    """必要なインデックスを作成（冪等）"""
    comments: Collection = db["comments"]
    comments.create_index([("farm_id", 1), ("created_at", DESCENDING)])
    comments.create_index([("user_id", 1)])

    analyses: Collection = db["photo_analyses"]
    analyses.create_index([("user_id", 1)])
    analyses.create_index([("analyzed_at", DESCENDING)])

# =============================================
# ユーティリティ
# =============================================
def _serialize(doc: dict) -> dict:
    """MongoDB の ObjectId を文字列に変換してJSON化可能にする"""
    if doc is None:
        return {}
    doc["_id"] = str(doc["_id"])
    return doc

# =============================================
# コメント CRUD
# =============================================

def get_comments(farm_id: str, limit: int = 50, skip: int = 0) -> list[dict]:
    """
    農地IDに紐づくコメントを新しい順で取得

    Args:
        farm_id: 農地ID（Supabase farms.id と紐付け）
        limit: 取得件数上限（ページネーション用）
        skip: スキップ件数

    Returns:
        コメントのリスト（_idは文字列化済み）
    """
    db = get_db()
    cursor = (
        db["comments"]
        .find({"farm_id": farm_id})
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return [_serialize(doc) for doc in cursor]


def create_comment(
    farm_id: str,
    user_id: str,
    user_name: str,
    text: str,
    photo_url: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> dict:
    """
    コメントを新規作成

    Args:
        farm_id:    農地ID
        user_id:    ユーザーID（Supabase users.id）
        user_name:  表示名
        text:       コメント本文
        photo_url:  添付写真URL（Supabase Storage）
        tags:       タグリスト（例: ['害虫', '施肥']）

    Returns:
        作成されたコメントドキュメント
    """
    db = get_db()
    now = datetime.utcnow()
    doc = {
        "farm_id": farm_id,
        "user_id": user_id,
        "user_name": user_name,
        "text": text.strip(),
        "photo_url": photo_url,
        "likes": 0,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }
    result = db["comments"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def like_comment(comment_id: str) -> int:
    """
    コメントにいいね（+1インクリメント）

    Returns:
        更新後のいいね数
    """
    db = get_db()
    result = db["comments"].find_one_and_update(
        {"_id": ObjectId(comment_id)},
        {"$inc": {"likes": 1}},
        return_document=True,
    )
    if result is None:
        raise ValueError(f"Comment {comment_id} not found")
    return result["likes"]


def delete_comment(comment_id: str, user_id: str) -> bool:
    """
    コメントを削除（投稿者本人のみ）

    Returns:
        削除成功: True / 権限なし or 存在しない: False
    """
    db = get_db()
    result = db["comments"].delete_one({
        "_id": ObjectId(comment_id),
        "user_id": user_id,  # 本人確認
    })
    return result.deleted_count > 0


def get_recent_comments(limit: int = 20) -> list[dict]:
    """全農地の最新コメントをタイムライン形式で取得（SNSフィード）"""
    db = get_db()
    cursor = (
        db["comments"]
        .find({})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )
    return [_serialize(doc) for doc in cursor]


# =============================================
# 写真解析ログ
# =============================================

def save_photo_analysis(
    user_id: str,
    original_url: str,
    exif_lat: Optional[float],
    exif_lon: Optional[float],
    matched_farm: Optional[str],
    ndvi_at_time: Optional[float],
) -> dict:
    """
    写真解析結果をログとして保存

    Args:
        user_id:      解析したユーザーID（未ログインの場合は 'anonymous'）
        original_url: Supabase StorageへのアップロードURL
        exif_lat/lon: 写真のGPS座標（なければ None）
        matched_farm: マッチした農地ID（Supabase）
        ndvi_at_time: マッチ時点のNDVI値

    Returns:
        保存されたドキュメント
    """
    db = get_db()
    doc = {
        "user_id": user_id,
        "original_url": original_url,
        "exif_lat": exif_lat,
        "exif_lon": exif_lon,
        "matched_farm": matched_farm,
        "ndvi_at_time": ndvi_at_time,
        "analyzed_at": datetime.utcnow(),
    }
    result = db["photo_analyses"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def get_user_analyses(user_id: str, limit: int = 10) -> list[dict]:
    """ユーザーの写真解析履歴を取得"""
    db = get_db()
    cursor = (
        db["photo_analyses"]
        .find({"user_id": user_id})
        .sort("analyzed_at", DESCENDING)
        .limit(limit)
    )
    return [_serialize(doc) for doc in cursor]


# =============================================
# ヘルスチェック
# =============================================

def mongo_health() -> dict:
    """MongoDB接続状態の確認"""
    try:
        db = get_db()
        db.command("ping")
        comments_count = db["comments"].count_documents({})
        return {
            "status": "ok",
            "comments_total": comments_count,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
