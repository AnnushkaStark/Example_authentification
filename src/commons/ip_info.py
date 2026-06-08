import ipinfo

from src.config.configs import ip_info_settings


class IpIfoClient:
    def __init__(self):
        self.token = ip_info_settings.IP_INFO_TOKEN
        self.handler = None

    async def get_user_location(self, ip: str) -> dict[str, str | None]:
        if not self.handler:
            self.handler = ipinfo.getHandlerAsync(self.token)

        details = await self.handler.getDetails(ip)
        return {
            "country": details.all.get("country"),
            "city": details.all.get("city"),
        }

    async def get_user_locale(self, ip: str) -> str:
        location = await self.get_user_location(ip=ip)
        return location["country"]
