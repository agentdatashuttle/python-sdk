import logging, os
import socketio
from ..models.models import ADSRabbitMQClientParams, ADSBridgeClientParams

logLevel = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

# ADSRabbitMQClient - Used by ADSPublisher to connect to RabbitMQ broker and publish events
class ADSRabbitMQClient:
    ADS_WORKER_QUEUE_NAME = "ads_events_worker_queue"

    rabbitmq_client_params: ADSRabbitMQClientParams = None  # This will hold the parameters for the ADS client
    connection = None

    def __init__(self, rabbitmq_client_params: ADSRabbitMQClientParams):
        self.rabbitmq_client_params = rabbitmq_client_params
        self.connection = None

        self.connect()
        self.create_ads_worker_queue_if_not_exists()

    def connect(self):
        """
        Connect to the RabbitMQ broker.
        """
        import pika  # Importing here to avoid dependency issues if not used
        credentials = pika.PlainCredentials(self.rabbitmq_client_params.username, self.rabbitmq_client_params.password)
        parameters = pika.ConnectionParameters(host=self.rabbitmq_client_params.host, port=self.rabbitmq_client_params.port, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        logger.info("Connected to RabbitMQ broker.")

    def disconnect(self):
        """
        Disconnect from the RabbitMQ broker.
        """
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from RabbitMQ broker.")

    def is_connected(self) -> bool:
        """
        Check if the client is connected to the RabbitMQ broker.
        """
        return self.connection is not None and self.connection.is_open
    
    def get_channel(self):
        """
        Get a channel from the current connection.
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to RabbitMQ broker.")
        return self.connection.channel()
    
    def create_ads_worker_queue_if_not_exists(self):
        """
        Create a RabbitMQ Worker Queue if it does not already exist.
        """
        channel = self.get_channel()
        channel.queue_declare(queue=self.ADS_WORKER_QUEUE_NAME, durable=True)
        logger.info(f"RabbitMQ Worker Queue '{self.ADS_WORKER_QUEUE_NAME}' created or already exists.")
        channel.close()

    def __del__(self):
        """
        Ensure the connection is closed when the client is deleted.
        """
        self.disconnect()
        logger.info("ADSRabbitMQClient instance deleted and connection closed.")


# ADSBridgeClient - Used by ADSSubscriber to connect to ADS Bridge via Socket.io and hear for events
class ADSBridgeClient:
    def __init__(self, bridge_client_params: ADSBridgeClientParams):
        self.bridge_client_params = bridge_client_params
        
        self.socket_io_client = socketio.Client(
            reconnection=True,
            reconnection_attempts=5
        )

        @self.socket_io_client.event
        def connect():
            logger.info("Connected to ADS Bridge via Socket.io.")

        @self.socket_io_client.event
        def disconnect():
            logger.info("Disconnected from ADS Bridge.")

        @self.socket_io_client.event
        def connect_error(data):
            logger.error("Socket.io connection to ADS Bridge failed: %s", data)

        self.connect()


    def connect(self):
        """
        Connect to the ADS Bridge via Socket.io.
        """        
        self.socket_io_client.connect(
                                        url=self.bridge_client_params.connection_string,
                                        socketio_path=self.bridge_client_params.path_prefix + "/socket.io" if self.bridge_client_params.path_prefix != "/" else "/socket.io",
                                        auth={"ads_subscribers_pool_id": self.bridge_client_params.ads_subscribers_pool_id}
                                    )

    def disconnect(self):
        """
        Disconnect from the ADS Bridge.
        """
        if self.socket_io_client:
            self.socket_io_client.disconnect()

    def is_connected(self) -> bool:
        """
        Check if the client is connected to the ADS Bridge.
        """
        return self.socket_io_client is not None and self.socket_io_client.connected

    def __del__(self):
        """
        Ensure the connection is closed when the client is deleted.
        """
        self.disconnect()
        logger.info("ADSBridgeClient instance deleted and connection closed.")