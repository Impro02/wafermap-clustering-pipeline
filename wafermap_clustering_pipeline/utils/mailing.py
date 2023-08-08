# MODULES
import smtplib
from logging import Logger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# CONFIGS
from ..configs.config import MailingConfig


def send_mail(
    host: str, port: int, sender: str, receiver: str, subject: str, msg_html: str
):

    message = MIMEMultipart("alternative")

    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(msg_html, "html"))
    # Create secure connection with server and send email
    # context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.sendmail(sender, receiver, message.as_string())


def send_mail_error(
    file: str,
    error_path: str,
    config: MailingConfig,
    logger: Logger = None,
) -> str:
    message_error = f"{file=} processing failed, moved to {error_path}"

    html = f"""\
        <html>
            <body>
                <p>{message_error}</p>
            </body>
        </html>
    """

    try:
        send_mail(
            host=config.host,
            port=config.port,
            sender=config.sender,
            receiver=config.receiver,
            subject=f"Clustering - Error on {file}",
            msg_html=html,
        )
    except Exception as ex:
        if logger is not None:
            logger.critical("Unable to send error email", exc_info=ex)

    return message_error
