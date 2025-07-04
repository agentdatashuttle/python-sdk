import logging, os
from abc import ABC, abstractmethod
from datetime import datetime
import markdown
from slackify_markdown import slackify_markdown
from ..models.models import ADSDataPayload
import yagmail
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logLevel = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

# ADSNotificationEngine - Base class that all other notification modules inherit
class ADSNotificationEngine(ABC):
    """Base class that all other notification modules inherit from"""
    
    def __init__(self, agent_description: str):
        """Initialize the notification engine with an agent description
        
        Args:
            agent_description (str): Description of the agent using this notification engine
        """
        self._agent_description = agent_description
        self._ADS_DEVELOPER_PORTAL_URL = "https://agentdatashuttle.knowyours.co"  # TODO: Replace with actual URL
    
    def get_notification_body_markdown(self, body_payload: str) -> str:
        """Generate a markdown-formatted notification body
        
        Args:
            body_payload (str): The main content of the notification
            
        Returns:
            str: Formatted markdown string containing the notification
        """
        timestamp = datetime.utcnow().strftime("%d/%m/%Y - %H:%M:%S")
        
        ellipsis_ads_subscriber_agent_description = (
            f"{self._agent_description[:100]}..."
            if len(self._agent_description) > 100
            else self._agent_description
        )
        
        return f"## 🚀 Notification from ADS (Agent Data Shuttle)\n\n**Timestamp (UTC):** {timestamp}\n\n**Triggered Agent's Description:** {ellipsis_ads_subscriber_agent_description}\n\n---\n\n### Execution Summary\n\n\n{body_payload}\n\n---\n\n> Sent by **Agent Data Shuttle**\n\n> See more about ADS on _{self._ADS_DEVELOPER_PORTAL_URL}_\n\n"
    
    def get_notification_body_html(self, body_payload: str) -> str:
        """Generate an HTML-formatted notification body
        
        Args:
            body_payload (str): The main content of the notification
            
        Returns:
            str: Formatted HTML string containing the notification
        """
        timestamp = datetime.utcnow().strftime("%d/%m/%Y - %H:%M:%S")
        
        ellipsis_ads_subscriber_agent_description = (
            f"{self._agent_description[:100]}..."
            if len(self._agent_description) > 100
            else self._agent_description
        )
        
        # Convert Markdown to HTML
        try:
            html_payload = markdown.markdown(body_payload)
        except Exception as error:
            logger.error(f"Error converting Markdown to HTML: {error}")
            html_payload = f"<pre>{body_payload}</pre>"
            
        return f"""
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>ADS Notification</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        @media only screen and (max-width: 640px) {{
                            .container {{
                                width: 90% !important;
                                padding: 24px !important;
                            }}
                            .header {{
                                padding: 20px !important;
                                font-size: 20px !important;
                            }}
                        }}
                    </style>
                </head>
                <body style="margin:0; padding:0; background-color:#f5f5f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#f5f5f7">
                        <tr>
                            <td align="center" style="padding: 30px 10px;">
                                <table role="presentation" class="container" width="720" cellspacing="0" cellpadding="0" border="0" style="background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.06); width: 720px; max-width: 95%;">
                                    <tr>
                                        <td class="header" style="background: #1c1c1e; padding: 24px 32px; color: #f5f5f7; font-size: 22px; font-weight: 600; letter-spacing: 0.3px;">
                                            🚀 Notification from ADS (Agent Data Shuttle)
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 28px 40px; color: #1c1c1e;">
                                            <p style="margin: 0 0 10px; font-size: 14px; color: #555;"><strong style="color:#1c1c1e;">Timestamp (UTC):</strong> {timestamp}</p>
                                            <p style="margin: 0 0 20px; font-size: 14px; color: #555;"><strong style="color:#1c1c1e;">Triggered Agent's Description:</strong> {ellipsis_ads_subscriber_agent_description}</p>
                                            <div style="border-top: 1px solid #e0e0e0; margin: 20px 0;"></div>
                                            <h3 style="margin: 0 0 16px; font-size: 18px; font-weight: 500; color: #1c1c1e;">Execution Summary</h3>
                                            <div style="background: #f2f2f2; padding: 16px 20px; border-radius: 8px; font-size: 14px; line-height: 1.6; color: #333; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                                                {html_payload}
                                            </div>
                                            <div style="border-top: 1px solid #e0e0e0; margin: 20px 0;"></div>
                                            <p style="font-size: 12px; color: #888; margin: 0 0 4px;">Sent by <strong>Agent Data Shuttle</strong></p>
                                            <p style="font-size: 12px; color: #888; margin: 0;">See more about ADS on <em>{self._ADS_DEVELOPER_PORTAL_URL}</em></p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
            </html>
            """

    @abstractmethod
    def fire_notification(self, body_payload: str) -> bool:
        """Abstract method to be implemented by subclasses to send notification
        
        Args:
            body_payload (str): The content to be sent in the notification
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Abstract property to be implemented by subclasses to return the channel name
        
        Returns:
            str: The name of the notification channel
        """
        pass



# EmailNotificationChannel - Class that can be used to send emails
class EmailNotificationChannel(ADSNotificationEngine):
    """Class that can be used to send emails via SMTP."""
    def __init__(
        self,
        agent_description: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email_address: str,
        to_email_address: str,
        subject: str = "Notification from ADS Subscriber"
    ):
        if not all([
            smtp_host, smtp_port, smtp_username, smtp_password, from_email_address, to_email_address
        ]):
            err_msg = (
                "SMTP configuration needs all fields: host, port, smtp_username, smtp_password, "
                "from_email_address, to_email_address."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
        if smtp_port not in (465, 587):
            err_msg = "SMTP port must be either 465 (secure) or 587 (non-secure)."
            logger.error(err_msg)
            raise ValueError(err_msg)
        super().__init__(agent_description)
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_username = smtp_username
        self._smtp_password = smtp_password
        self._from_email_address = from_email_address
        self._to_email_address = to_email_address
        self._subject = subject

        # Setup yagmail SMTP client
        self._yag = yagmail.SMTP(
            user=self._smtp_username,
            password=self._smtp_password,
            host=self._smtp_host,
            port=self._smtp_port,
            smtp_starttls=(self._smtp_port == 587),
            smtp_ssl=(self._smtp_port == 465)
        )

    @property
    def channel_name(self) -> str:
        return "EmailNotificationChannel"

    def fire_notification(self, body_payload: str) -> bool:
        try:
            mail_html_body = self.get_notification_body_html(body_payload)
            self._yag.send(
                to=self._to_email_address,
                subject=self._subject,
                contents=[mail_html_body],
                prettify_html=False
            )
            logger.info(f"Email sent successfully to '{self._to_email_address}'")
            return True
        except Exception as error:
            logger.warning(f"Failed to send email notification: {error}")
            return False

# SlackNotificationChannel - Class that can be used to send slack notifications
class SlackNotificationChannel(ADSNotificationEngine):
    """Class that can be used to send Slack notifications."""
    def __init__(
        self,
        agent_description: str,
        slack_bot_token: str,
        slack_channel_name: str
    ):
        if not all([
            agent_description, slack_bot_token, slack_channel_name
        ]):
            err_msg = (
                "Slack configuration needs all fields: agent_description, slack_bot_token, slack_channel_name."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
        super().__init__(agent_description)
        self._slack_bot_token = slack_bot_token
        self._slack_channel_name = slack_channel_name
        try:
            self._slack_web_client = WebClient(token=self._slack_bot_token)
        except Exception as error:
            logger.error("Failed to initialize Slack WebClient. Please check your Slack bot token.", exc_info=error)
            raise ValueError("Invalid Slack bot token")

    @property
    def channel_name(self) -> str:
        return "SlackNotificationChannel"

    def fire_notification(self, body_payload: str) -> bool:
        try:
            notif_md_body = self.get_notification_body_markdown(body_payload)
            slackified_md_body = slackify_markdown(notif_md_body)
            response = self._slack_web_client.chat_postMessage(
                channel=self._slack_channel_name,
                text=slackified_md_body
            )
            logger.info(f"Slack notification sent successfully to '{self._slack_channel_name}'")
            logger.debug(f"Slack Message info: {response}")
            return True
        except SlackApiError as error:
            logger.warning(f"Failed to send Slack notification: {error.response['error']}")
            return False
        except Exception as error:
            logger.warning(f"Failed to send Slack notification: {error}")
            return False
