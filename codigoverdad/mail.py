import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "ekmotion2023@gmail.com"  # address
password = "yxdawgmgjwfqpwjn"


def emailverify(sendto: str, message: str, attachment_path: str):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        try:
            server.login(sender_email, password)

            # Create a multipart message and set headers
            email_message = MIMEMultipart()
            email_message["From"] = sender_email
            email_message["To"] = sendto
            email_message["Subject"] = "Email Verification"

            # Attach the message content
            email_message.attach(MIMEText(message, "plain"))

            # Attach the file
            with open(attachment_path, "rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment_path.split('/')[-1]}",
            )
            email_message.attach(part)

            # Send the email
            server.send_message(email_message)
        except Exception as error:
            print(error)


# Usage example
sendto = "edu.marin.vera@gmail.com"
message = "Este es tu señal ECG, - Diego."
attachment_path = "./saves/pac1.json"

emailverify(sendto, message, attachment_path)
