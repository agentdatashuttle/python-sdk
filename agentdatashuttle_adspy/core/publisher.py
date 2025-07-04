import logging, os
import pika
from .client import ADSRabbitMQClient, ADSRabbitMQClientParams
from ..models.models import ADSDataPayload

logLevel = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

class ADSPublisher:
    rabbitmq_client_params: ADSRabbitMQClientParams = None
    publisher_name: str = None  
    ads_rabbitmq_client: ADSRabbitMQClient = None

    def __init__(self, publisher_name: str, rabbitmq_client_params: ADSRabbitMQClientParams):
        self.publisher_name = publisher_name
        self.rabbitmq_client_params = rabbitmq_client_params
        self.ads_rabbitmq_client = ADSRabbitMQClient(rabbitmq_client_params)

    def publish_event(self, event_payload: ADSDataPayload):
        """
        Publish an event to the ADS events worker queue.
        """
        if not self.ads_rabbitmq_client.is_connected():
            raise ConnectionError("ADSRabbitMQClient is not connected to the RabbitMQ broker.")
        
        try:
            channel = self.ads_rabbitmq_client.get_channel()
            message = event_payload.model_dump_json()
            channel.basic_publish(
                                    exchange='',
                                    routing_key=self.ads_rabbitmq_client.ADS_WORKER_QUEUE_NAME,
                                    body=message,
                                    properties=pika.BasicProperties(
                                                    delivery_mode = pika.DeliveryMode.Persistent
                                                )
                                )
            
            logger.debug(f"ADS Event published: {event_payload}")
        except Exception as e:
            logger.error(f"Error publishing ADS event: {e}", e)
        finally:
            channel.close()