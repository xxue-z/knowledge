import json
import logging
from datetime import datetime, date, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.heatmap import SearchEvent, HeatmapStats

logger = logging.getLogger(__name__)


class HeatmapService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_search(
        self,
        query_text: str,
        query_embedding: list[float] | None,
        user_id: str | None,
        dept_id: str | None,
        hit_docs: list[dict],
        filter_conditions: dict | None,
        duration_ms: int,
    ):
        try:
            hit_doc_ids = [doc.get("id", "") for doc in hit_docs]
            hit_scores = [doc.get("score", 0) for doc in hit_docs]

            event = SearchEvent(
                query_text=query_text,
                query_embedding=json.dumps(query_embedding) if query_embedding else None,
                user_id=user_id,
                dept_id=dept_id,
                hit_doc_ids=hit_doc_ids,
                hit_scores=hit_scores,
                filter_conditions=filter_conditions,
                search_duration_ms=duration_ms,
            )
            self.db.add(event)
            await self.db.commit()

            redis = await get_redis()
            now = datetime.utcnow()
            
            await redis.zincrby("heatmap:queries:24h", 1, query_text)
            
            for doc_id in hit_doc_ids:
                if doc_id:
                    await redis.zincrby("heatmap:documents:24h", 1, doc_id)
            
            hour_key = f"heatmap:hour:{now.strftime('%Y-%m-%d:%H')}"
            await redis.incr(hour_key)
            await redis.expire(hour_key, 86400 * 7)

        except Exception as e:
            logger.error(f"Failed to record search event: {e}")
            await self.db.rollback()

    async def get_hot_queries(self, time_range: str = "24h", limit: int = 10) -> list[dict]:
        redis = await get_redis()
        
        if time_range == "24h":
            results = await redis.zrevrange("heatmap:queries:24h", 0, limit - 1, withscores=True)
        else:
            days = 7 if time_range == "7d" else 30
            start_date = date.today() - timedelta(days=days)
            
            stmt = (
                select(
                    HeatmapStats.stat_key,
                    func.sum(HeatmapStats.count).label("total_count"),
                )
                .where(HeatmapStats.stat_type == "query")
                .where(HeatmapStats.stat_date >= start_date)
                .group_by(HeatmapStats.stat_key)
                .order_by(func.sum(HeatmapStats.count).desc())
                .limit(limit)
            )
            db_results = await self.db.execute(stmt)
            results = [(row.stat_key, row.total_count) for row in db_results]

        return [
            {"rank": i + 1, "query": query, "count": int(count), "trend": "stable"}
            for i, (query, count) in enumerate(results)
        ]

    async def get_hot_documents(self, time_range: str = "24h", limit: int = 10) -> list[dict]:
        redis = await get_redis()
        
        if time_range == "24h":
            results = await redis.zrevrange("heatmap:documents:24h", 0, limit - 1, withscores=True)
        else:
            days = 7 if time_range == "7d" else 30
            start_date = date.today() - timedelta(days=days)
            
            stmt = (
                select(
                    HeatmapStats.stat_key,
                    func.sum(HeatmapStats.count).label("total_count"),
                )
                .where(HeatmapStats.stat_type == "document")
                .where(HeatmapStats.stat_date >= start_date)
                .group_by(HeatmapStats.stat_key)
                .order_by(func.sum(HeatmapStats.count).desc())
                .limit(limit)
            )
            db_results = await self.db.execute(stmt)
            results = [(row.stat_key, row.total_count) for row in db_results]

        return [
            {
                "rank": i + 1,
                "doc_id": doc_id,
                "doc_title": f"Document {doc_id}",
                "doc_type": "wiki",
                "hit_count": int(count),
                "avg_score": 0.0,
            }
            for i, (doc_id, count) in enumerate(results)
        ]

    async def get_timeline(self, target_date: str | None = None, granularity: str = "hour") -> dict:
        redis = await get_redis()
        
        if target_date is None:
            target_date = date.today().isoformat()
        
        if granularity == "hour":
            data = []
            for hour in range(24):
                key = f"heatmap:hour:{target_date}:{hour:02d}"
                count = await redis.get(key)
                data.append({"hour": hour, "count": int(count or 0)})
            
            peak_hour = max(data, key=lambda x: x["count"])["hour"] if data else 0
            total = sum(d["count"] for d in data)
            
            return {
                "date": target_date,
                "granularity": granularity,
                "data": data,
                "peak_hour": peak_hour,
                "total_count": total,
            }
        else:
            start_date = datetime.fromisoformat(target_date).date() - timedelta(days=6)
            
            stmt = (
                select(
                    HeatmapStats.stat_key,
                    func.sum(HeatmapStats.count).label("total_count"),
                )
                .where(HeatmapStats.stat_type == "hour")
                .where(HeatmapStats.stat_date >= start_date)
                .group_by(HeatmapStats.stat_key)
            )
            results = await self.db.execute(stmt)
            
            data = [{"day": row.stat_key, "count": row.total_count} for row in results]
            return {
                "date": target_date,
                "granularity": granularity,
                "data": data,
                "total_count": sum(d["count"] for d in data),
            }

    async def get_navigation_heat(self) -> list[dict]:
        stmt = (
            select(
                HeatmapStats.stat_key,
                func.sum(HeatmapStats.count).label("total_count"),
            )
            .where(HeatmapStats.stat_type == "navigation")
            .group_by(HeatmapStats.stat_key)
            .order_by(func.sum(HeatmapStats.count).desc())
        )
        results = await self.db.execute(stmt)
        
        return [
            {
                "node_id": row.stat_key,
                "node_name": f"Node {row.stat_key}",
                "path": f"/{row.stat_key}",
                "hit_count": row.total_count,
                "hot_level": "hot" if row.total_count > 100 else "warm" if row.total_count > 50 else "normal",
            }
            for row in results
        ]
