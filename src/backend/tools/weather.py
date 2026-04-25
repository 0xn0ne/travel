"""Weather query tool — checks weather forecast for a city (BIZ-02).

Per D-28, D-29, D-30, D-37:
- Calls AmapService.get_weather() which resolves city→adcode
- Returns formatted Chinese text with daily forecast and travel suggestions
"""

from agents import RunContextWrapper, function_tool

from backend.agent.context import AgentContext


def _weather_suggestion(dayweather: str) -> str:
    """Generate a travel suggestion based on weather conditions."""
    if any(w in dayweather for w in ["雨", "暴雨", "雷"]):
        return "建议带伞，适合室内活动"
    if any(w in dayweather for w in ["雪", "冰雹"]):
        return "注意保暖防滑，适合室内活动"
    if any(w in dayweather for w in ["晴", "多云"]):
        return "适合户外活动"
    if "阴" in dayweather:
        return "天气阴沉，可安排室内外结合的活动"
    if any(w in dayweather for w in ["雾", "霾"]):
        return "能见度较低，注意出行安全"
    return "适宜出行"


@function_tool
async def query_weather(
    ctx: RunContextWrapper[AgentContext],
    city: str,
    days: int = 3,
) -> str:
    """查询城市天气预报，帮助用户选择出行时间和准备物品。

    Args:
        city: 城市名称，如"上海"、"杭州"
        days: 查询天数，1-7天，默认3天
    """
    amap_service = ctx.context.amap_service

    try:
        data = await amap_service.get_weather(city_name=city, days=days)
    except Exception as e:
        return f"查询 {city} 天气失败: {e!s}"

    if "error" in data:
        return data["error"]

    lines = [f"📍 {city} 天气预报", ""]

    # Current conditions
    current = data.get("current", {})
    if current:
        lines.append(f"🌤 当前天气: {current.get('weather', '未知')}")
        lines.append(f"🌡 温度: {current.get('temperature', '未知')}°C")
        lines.append(f"💧 湿度: {current.get('humidity', '未知')}%")
        lines.append(f"🌬 风向风力: {current.get('winddirection', '未知')} {current.get('windpower', '未知')}级")
        lines.append(f"⏰ 更新时间: {current.get('reporttime', '未知')}")
        lines.append("")

    # Forecast
    forecast = data.get("forecast", [])
    if forecast:
        lines.append("📋 未来天气预报:")
        for day in forecast:
            date = day.get("date", "未知")
            day_w = day.get("dayweather", "未知")
            night_w = day.get("nightweather", "未知")
            high = day.get("daytemp", "?")
            low = day.get("nighttemp", "?")
            wind = day.get("daywind", "未知")
            power = day.get("daypower", "未知")

            suggestion = _weather_suggestion(day_w)

            lines.append(f"")
            lines.append(f"📅 {date}")
            lines.append(f"   白天: {day_w} | 夜间: {night_w}")
            lines.append(f"   温度: {low}°C ~ {high}°C")
            lines.append(f"   风力: {wind}风 {power}级")
            lines.append(f"   💡 {suggestion}")

    return "\n".join(lines)
