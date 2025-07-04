import logging, os
from .client import ADSBridgeClient, ADSBridgeClientParams

logLevel = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

class ADSDataConnector:
    ads_bridge_client: ADSBridgeClient = None # ADSBridgeClient in this case will have info to act as consumer of the Socket.io events from the ADS Bridge
    bridge_client_params: ADSBridgeClientParams = None  # This will hold the parameters for the ADS Bridge Client
    connector_name: str = None  # Name of the data connector
    ads_publish_socket_event_name: str = None  # Name of the event which will be published by the ADS Bridge for this connector

    def __init__(self, connector_name: str, bridge_client_params: ADSBridgeClientParams, ads_publish_socket_event_name: str = "ads_event_published"):
        self.connector_name = connector_name
        self.bridge_client_params = bridge_client_params
        self.ads_publish_socket_event_name = ads_publish_socket_event_name
        self.ads_bridge_client = ADSBridgeClient(bridge_client_params)

    def setup_callback(self, callback):
        """
        THREAD TARGET METHOD - Set up a callback function to process messages from the ADS Bridge.
        Pushes messages to the ADSSubscriber Job Queue once message is consumed.
        """
        if not self.ads_bridge_client.is_connected():
            raise ConnectionError("ADSBridgeClient is not connected to the ADS Bridge.")
        
        try:
            @self.ads_bridge_client.socket_io_client.on(self.ads_publish_socket_event_name)
            def socket_event_callback(msg):
                """
                Callback function to process messages from the ADS Bridge.
                This function should be set up in each data connector.
                """
                try:
                    logger.debug(f"Received message from ADS Bridge: {msg}")
                    callback(msg)  # Call the provided callback with the message - pushes the payload to the ADSSubscriber Job Queue
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)

            logger.info(f"Listening for events on '{self.ads_publish_socket_event_name}' for connector '{self.connector_name}'")
            self.ads_bridge_client.socket_io_client.wait()  # Keep the client running to listen for events
        except KeyboardInterrupt:
            logger.info(f"Stopping listening to ADS Bridge for connector: {self.connector_name}")
            self.ads_bridge_client.disconnect()
        except Exception as e:
            logger.error(f"Error in consuming events for connector '{self.connector_name}': {e}")