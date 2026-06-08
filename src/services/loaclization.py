from src.commons.ip_info import IpIfoClient


class LocalizationService:
    def __init__(self, client: IpIfoClient):
        self.client = client

    async def get_localization(self, request_headers: dict[str, str]) -> str:
        real_ip = request_headers.get("x-real-ip")

        if real_ip:
            real_ip = real_ip.split(",")[0].strip()
            country = await self.client.get_user_locale(ip=real_ip)

        match country:
            case "KZ":
                return "KZ"

            case _:
                return "RU"
