"""セッション読み込みモジュール"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional

from .models import SessionMessage


class SessionReader:
    """SQLiteセッションデータベース読み込み"""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).expanduser()
        self._conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> "SessionReader":
        """データベース接続"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"データベースが見つかりません: {self.db_path}")
        
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        return self
    
    def close(self):
        """接続終了"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self) -> "SessionReader":
        return self.connect()
    
    def __exit__(self, *args):
        self.close()
    
    def _parse_timestamp(self, ts: float) -> datetime:
        """Unix timestamp (REAL) を datetime に変換"""
        if ts is None:
            return datetime.now()
        return datetime.fromtimestamp(ts)
    
    def get_recent_sessions(self, limit: int = 100) -> List[dict]:
        """最近のセッション一覧を取得"""
        if not self._conn:
            self.connect()
        
        cursor = self._conn.execute(
            """
            SELECT s.id as session_id, s.title, s.started_at as created_at, 
                   s.ended_at as updated_at, s.message_count
            FROM sessions s
            ORDER BY s.started_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_messages_for_session(
        self,
        session_id: str,
        since: Optional[datetime] = None
    ) -> Iterator[SessionMessage]:
        """特定セッションのメッセージを取得"""
        if not self._conn:
            self.connect()
        
        query = "SELECT * FROM messages WHERE session_id = ?"
        params: list = [session_id]
        
        if since:
            query += " AND timestamp > ?"
            params.append(since.timestamp())
        
        query += " ORDER BY timestamp ASC"
        
        cursor = self._conn.execute(query, params)
        
        for row in cursor:
            yield SessionMessage(
                id=str(row["id"]),
                role=row["role"],
                content=row["content"] or "",
                timestamp=self._parse_timestamp(row["timestamp"]),
                session_id=row["session_id"],
                metadata=self._parse_metadata(row["tool_calls"] or "{}")
            )
    
    def get_all_messages(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Iterator[SessionMessage]:
        """全メッセージを取得（バッチ処理対応）"""
        if not self._conn:
            self.connect()
        
        query = "SELECT * FROM messages"
        params: list = []
        
        if since:
            query += " WHERE timestamp > ?"
            params.append(since.timestamp())
        
        query += " ORDER BY timestamp ASC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self._conn.execute(query, params)
        
        for row in cursor:
            yield SessionMessage(
                id=str(row["id"]),
                role=row["role"],
                content=row["content"] or "",
                timestamp=self._parse_timestamp(row["timestamp"]),
                session_id=row["session_id"],
                metadata=self._parse_metadata(row["tool_calls"] or "{}")
            )
    
    def _parse_metadata(self, metadata_str: str) -> dict:
        """メタデータJSONをパース。Hermesのtool_callsはlistの場合があるのでdictに正規化"""
        import json
        try:
            data = json.loads(metadata_str) if metadata_str else {}
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"tool_calls": data}
            return {"value": data}
        except json.JSONDecodeError:
            return {}
