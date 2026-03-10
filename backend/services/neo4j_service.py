"""
SATELLITE PRO - Neo4j AuraDB グラフ操作サービス
農家-農地関係・SNSフォロー・農地隣接グラフを管理

接続: neo4j+s://xxxx.databases.neo4j.io
"""
import os
from typing import Optional
from contextlib import contextmanager

# neo4j ドライバー（requirements.txtに追加済み）
try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

# =============================================
# 接続管理（シングルトン）
# =============================================
_driver: Optional["Driver"] = None

def get_driver():
    """Neo4j ドライバーのシングルトン取得"""
    global _driver
    if not NEO4J_AVAILABLE:
        raise RuntimeError("neo4j パッケージがインストールされていません")
    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASS")
        if not uri or not password:
            raise RuntimeError("NEO4J_URI または NEO4J_PASS が未設定です")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
        # 接続テスト
        _driver.verify_connectivity()
    return _driver

@contextmanager
def get_session():
    """Noe4j セッションのコンテキストマネージャー"""
    driver = get_driver()
    with driver.session() as session:
        yield session

# =============================================
# ユーザー・農地グラフ操作
# =============================================

def upsert_user(user_id: str, email: str, display_name: str, prefecture: str = ""):
    """
    ユーザーノードを作成または更新（MERGE）
    Supabase Auth のサインアップ時に呼び出す
    """
    with get_session() as session:
        session.run("""
            MERGE (u:User {id: $id})
            ON CREATE SET
                u.email = $email,
                u.display_name = $display_name,
                u.prefecture = $prefecture,
                u.created_at = datetime()
            ON MATCH SET
                u.display_name = $display_name,
                u.updated_at = datetime()
        """, id=user_id, email=email, display_name=display_name, prefecture=prefecture)


def upsert_farm(farm_id: str, name: str, prefecture_id: str, lat: float, lon: float):
    """
    農地ノードを作成または更新し、都道府県ノードと紐付ける
    """
    with get_session() as session:
        session.run("""
            MERGE (f:Farm {id: $farm_id})
            ON CREATE SET
                f.name = $name,
                f.lat = $lat,
                f.lon = $lon,
                f.created_at = datetime()
            ON MATCH SET
                f.name = $name,
                f.updated_at = datetime()
            WITH f
            MERGE (p:Prefecture {id: $pref_id})
            ON CREATE SET p.name = $pref_id
            MERGE (f)-[:LOCATED_IN]->(p)
        """, farm_id=farm_id, name=name, pref_id=prefecture_id, lat=lat, lon=lon)


def link_user_to_farm(user_id: str, farm_id: str):
    """ユーザーが農地を所有する関係を作成"""
    with get_session() as session:
        session.run("""
            MATCH (u:User {id: $uid}), (f:Farm {id: $fid})
            MERGE (u)-[:OWNS]->(f)
        """, uid=user_id, fid=farm_id)


def add_comment_to_graph(user_id: str, farm_id: str, comment_id: str):
    """
    コメントノードをグラフに追加
    (User)-[:POSTED]->(Comment)-[:ON]->(Farm)
    comment_id は MongoDB の _id 文字列
    """
    with get_session() as session:
        session.run("""
            CREATE (c:Comment {id: $cid, created_at: datetime()})
            WITH c
            MATCH (u:User {id: $uid}), (f:Farm {id: $fid})
            CREATE (u)-[:POSTED]->(c)
            CREATE (c)-[:ON]->(f)
        """, cid=comment_id, uid=user_id, fid=farm_id)


# =============================================
# フォロー関係
# =============================================

def follow_farm(user_id: str, farm_id: str):
    """ユーザーが農地をフォロー（ウォッチ）"""
    with get_session() as session:
        session.run("""
            MATCH (u:User {id: $uid}), (f:Farm {id: $fid})
            MERGE (u)-[:FOLLOWS {since: date()}]->(f)
        """, uid=user_id, fid=farm_id)


def unfollow_farm(user_id: str, farm_id: str):
    """フォロー解除"""
    with get_session() as session:
        session.run("""
            MATCH (u:User {id: $uid})-[r:FOLLOWS]->(f:Farm {id: $fid})
            DELETE r
        """, uid=user_id, fid=farm_id)


def follow_user(follower_id: str, followee_id: str):
    """農家同士のフォロー"""
    with get_session() as session:
        session.run("""
            MATCH (u1:User {id: $from_id}), (u2:User {id: $to_id})
            MERGE (u1)-[:FOLLOWS_USER {since: date()}]->(u2)
        """, from_id=follower_id, to_id=followee_id)


# =============================================
# クエリ（フィード・推薦）
# =============================================

def get_user_timeline(user_id: str, limit: int = 20) -> list[dict]:
    """
    ユーザーがフォローしている農地の最新コメントを取得
    """
    with get_session() as session:
        result = session.run("""
            MATCH (u:User {id: $uid})-[:FOLLOWS]->(f:Farm)
            MATCH (author:User)-[:POSTED]->(c:Comment)-[:ON]->(f)
            RETURN
                f.id AS farm_id,
                f.name AS farm_name,
                author.display_name AS author,
                c.id AS comment_id,
                c.created_at AS posted_at
            ORDER BY c.created_at DESC
            LIMIT $limit
        """, uid=user_id, limit=limit)
        return [dict(r) for r in result]


def get_farm_community(farm_id: str) -> list[dict]:
    """農地のコミュニティ参加者（オーナー+コメント投稿者）を返す"""
    with get_session() as session:
        result = session.run("""
            MATCH (u:User)-[:OWNS]->(f:Farm {id: $fid})
            WITH collect(DISTINCT {id: u.id, name: u.display_name, role: 'owner'}) AS owners
            MATCH (commenter:User)-[:POSTED]->(:Comment)-[:ON]->(f:Farm {id: $fid})
            WITH owners, collect(DISTINCT {id: commenter.id, name: commenter.display_name, role: 'commenter'}) AS commenters
            RETURN owners + commenters AS members
        """, fid=farm_id)
        rows = list(result)
        if rows:
            return rows[0]["members"]
        return []


def get_similar_farms(farm_id: str, limit: int = 5) -> list[dict]:
    """
    農地隣接グラフから近隣農地を推薦
    （事前に link_adjacent_farms() で隣接関係を構築しておく必要あり）
    """
    with get_session() as session:
        result = session.run("""
            MATCH (f:Farm {id: $fid})-[:ADJACENT_TO]-(neighbor:Farm)
            RETURN neighbor.id AS farm_id, neighbor.name AS name, neighbor.lat AS lat, neighbor.lon AS lon
            LIMIT $limit
        """, fid=farm_id, limit=limit)
        return [dict(r) for r in result]


def link_adjacent_farms(max_distance_km: float = 50.0):
    """
    同一都道府県内で50km以内の農地を ADJACENT_TO で接続
    data_processor_v2.py から定期実行
    """
    with get_session() as session:
        session.run("""
            MATCH (f1:Farm)-[:LOCATED_IN]->(p:Prefecture)<-[:LOCATED_IN]-(f2:Farm)
            WHERE f1.id < f2.id
              AND point.distance(
                point({latitude: f1.lat, longitude: f1.lon}),
                point({latitude: f2.lat, longitude: f2.lon})
              ) < $max_m
            MERGE (f1)-[:ADJACENT_TO]-(f2)
        """, max_m=max_distance_km * 1000)


# =============================================
# 初期データ投入（47都道府県ノード）
# =============================================

def init_prefecture_nodes(prefectures: list[dict]):
    """
    47都道府県ノードを一括作成
    data_processor_v2.py の main() 最初に呼び出す
    """
    with get_session() as session:
        session.run("""
            UNWIND $prefs AS pref
            MERGE (p:Prefecture {id: pref.id})
            ON CREATE SET p.name = pref.name, p.lat = pref.lat, p.lon = pref.lon
        """, prefs=prefectures)


# =============================================
# ヘルスチェック
# =============================================

def neo4j_health() -> dict:
    """Neo4j接続ヘルスチェック"""
    if not NEO4J_AVAILABLE:
        return {"status": "unavailable", "error": "neo4j package not installed"}
    try:
        with get_session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS total")
            total = result.single()["total"]
        return {"status": "ok", "total_nodes": total}
    except Exception as e:
        return {"status": "error", "error": str(e)}
