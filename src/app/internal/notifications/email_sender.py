from email.message import EmailMessage
import aiosmtplib


class EmailSender:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
        timeout: int = 10,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls
        self.timeout = timeout

    async def send(
        self,
        recipient: str,
        subject: str,
        text: str,
    ):
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = recipient
        message["Subject"] = subject

        message.set_content(text)


        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
            timeout=self.timeout,
        )