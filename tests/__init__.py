class TestBase:
    api_base_url = "/auth/api/"


class TestAuthBase(TestBase):
    root_url = f"{TestBase.api_base_url}auth/"


class TestVerificationBase(TestBase):
    root_url = f"{TestBase.api_base_url}verification/"


class TestLocalizationBase(TestBase):
    root_url = f"{TestBase.api_base_url}localization/"
