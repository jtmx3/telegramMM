"""
services/stats_service.py
Formats statistics gathered from ExcelService into a display-ready string.
"""

from services.excel_service import ExcelService


class StatsService:
    def __init__(self, excel_service: ExcelService):
        self._excel_service = excel_service

    async def build_report(self) -> str:
        stats = await self._excel_service.get_statistics()

        lines = [
            "📊 <b>Statistics</b>",
            "",
            f"📢 Total Channels: <b>{stats['total_channels']}</b>",
            f"👥 Total Members: <b>{stats['total_members']}</b>",
            f"🗑 Total Removed (all time): <b>{stats['total_removed']}</b>",
            "",
            "📆 <b>Today</b>",
            f"➕ Adds: <b>{stats['today_adds']}</b>",
            f"➖ Removes: <b>{stats['today_removes']}</b>",
            f"♻ Unbans: <b>{stats['today_unbans']}</b>",
            "",
            "📋 <b>Members per Channel</b>",
        ]

        per_channel = stats["members_per_channel"]
        if per_channel:
            for name, count in per_channel.items():
                lines.append(f"   • {name}: <b>{count}</b>")
        else:
            lines.append("   (no channels yet)")

        return "\n".join(lines)
