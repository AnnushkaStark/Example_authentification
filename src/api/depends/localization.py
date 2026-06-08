from typing import Annotated

from fastapi import Depends

from src.commons.ip_info import IpIfoClient
from src.services.loaclization import LocalizationService


def get_ip_info_client() -> IpIfoClient:
    return IpIfoClient()


ApiInfoClentDepends = Annotated[IpIfoClient, Depends(get_ip_info_client)]


def get_localozation_serive(
    client: ApiInfoClentDepends,
) -> LocalizationService:
    return LocalizationService(client=client)


LocalizationServiceDepends = Annotated[
    LocalizationService, Depends(get_localozation_serive)
]
