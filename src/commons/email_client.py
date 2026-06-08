from typing import Annotated

from dddshared.logger import log
from fastapi import File
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig
from fastapi_mail import FastMail
from fastapi_mail import MessageSchema
from fastapi_mail.schemas import MessageType
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape
from pydantic import EmailStr

from src.config.configs import email_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes

env = Environment(
    loader=FileSystemLoader("src/templates"),
    enable_async=True,
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailClient:
    async def send_mail(
        self,
        recepients: list[EmailStr],
        template_body: dict,
        template: str = "verification.html",
        subject: str = "",
        attachments: Annotated[list[UploadFile], File(None)] = None,
    ) -> dict:
        template = env.get_template(template)
        html = await template.render_async(subject=subject, **template_body)
        massage = MessageSchema(
            recipients=recepients,
            subject=subject,
            template_body=html,
            attachments=attachments,
            subtype=MessageType.html,
        )
        conf = ConnectionConfig(
            MAIL_USERNAME=email_settings.MAIL_USERNAME,
            MAIL_PASSWORD=email_settings.MAIL_PASSWORD,
            MAIL_FROM=email_settings.MAIL_FROM,
            MAIL_PORT=email_settings.MAIL_PORT,
            MAIL_SERVER=email_settings.MAIL_SERVER,
            MAIL_STARTTLS=email_settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=email_settings.MAIL_SSL_TLS,
        )
        fast_mail = FastMail(config=conf)
        try:
            log.system.info(
                f"Отправка почтового уведомлеия получателю {recepients[0]}"
            )
            await fast_mail.send_message(message=massage)
        except Exception as err:
            log.system.error(f"Ошибка отправки почтовго уведомления {err}")
            raise DomainError(ErrorCodes.ERROR_SEND_MAIL) from err

        log.system.info(
            f"Уведомление получателю {recepients[0]} успешно отправлено"
        )
        return {"message": "Message sent successfully if status_code is 1"}
