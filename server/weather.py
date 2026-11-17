"""Open-Meteo (no API key). Returns None on any failure; callers must cope."""
import httpx

_geo_cache: dict = {}


async def _geocode(c: httpx.AsyncClient, location: str):
    if location in _geo_cache:
        return _geo_cache[location]
    parts = [p.strip() for p in location.split(",") if p.strip()]
    for name in [location, *reversed(parts)]:
        r = await c.get("https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": name, "count": 1, "country_code": "PK"})
        res = r.json().get("results")
        if res:
            _geo_cache[location] = res[0]
            return res[0]
    return None


async def get_weather(location: str):
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            g = await _geocode(c, location)
            if not g:
                return None
            r = await c.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": g["latitude"], "longitude": g["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                         "precipitation_probability_max,relative_humidity_2m_mean",
                "forecast_days": 5, "timezone": "Asia/Karachi"})
            j = r.json()
            return {"place": f"{g['name']}, {g.get('admin1','')}", "current": j["current"], "daily": j["daily"]}
    except Exception:
        return None
