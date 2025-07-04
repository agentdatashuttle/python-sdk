import logging, threading, time, os
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from typing import List
from .dataconnector import ADSDataConnector
from .notifications import ADSNotificationEngine
from ..models.models import ADSDataPayload
from ..utils.prompts import get_event_contextualization_prompt

logLevel = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=logLevel)
logger = logging.getLogger(__name__)

class ADSSubscriber:
    data_connectors: List[ADSDataConnector] = []
    agent_callback_function: callable = None # Will take in "agent_prompt" as argument and return the "agent_response"
    agent_description: str = None
    notification_channels: List[ADSNotificationEngine] = [] # This will hold the notification channels for the ADS events
    llm: BaseChatModel = None
    ads_events_job_queue: List[ADSDataPayload] = [] # This will hold the job queue for the ADS events and process in the main thread

    def __init__(self, agent_callback_function: callable, llm: BaseChatModel, agent_description: str, data_connectors: List[ADSDataConnector], notification_channels: List[ADSNotificationEngine] = []):
        self.data_connectors = data_connectors
        self.agent_callback_function = agent_callback_function
        self.agent_description = agent_description
        self.llm = llm
        self.notification_channels = notification_channels
        self.ads_events_job_queue = []  # Initialize the job queue for ADS events

        # Check if the agent callback function is callable and has the expected signature
        if not callable(self.agent_callback_function) and not hasattr(self.agent_callback_function, '__call__'):
            raise ValueError("agent_callback_function must be a callable that takes in 'agent_prompt' and returns 'agent_response'.")

    def _generate_agent_invocation_prompt(self, ads_event_payload: ADSDataPayload) -> str:
        try:
            if not self.agent_description:
                raise ValueError("Agent description is not set.")
            if not isinstance(ads_event_payload, ADSDataPayload):
                raise TypeError("ads_event_payload must be an instance of ADSDataPayload.")
                
            prompt = get_event_contextualization_prompt(self.agent_description, ads_event_payload)
            response = self.llm.with_retry(stop_after_attempt=5).invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating agent invocation prompt: {e}",e)
            return None

    def _socket_event_callback(self, msg):
        """
        Callback function to process messages from the ADSBridge.
        This function should be set up in each data connector.
        """
        try:
            message_payload = ADSDataPayload.model_validate_json(msg, strict=True)
            self.ads_events_job_queue.append(message_payload)  # Push the payload to the job queue
            logger.debug(f"Pushed message from ADS Bridge into ADS Subscriber Job Queue: {message_payload}")
        except Exception as e:
            logger.error(f"Error pushing message to job queue: {e}", exc_info=True)

    def _process_ads_event_job_callback(self, event_payload: ADSDataPayload):
        try:
            logger.debug(f"Processing message from job queue: {event_payload}")

            # Generate the agent invocation prompt based on the received message
            agent_invocation_prompt = self._generate_agent_invocation_prompt(event_payload)

            if not agent_invocation_prompt:
                logger.error("Failed to generate agent invocation prompt.")
                return

            # Use the generated prompt to invoke the agent
            logger.debug("Invoking agent with the ADS event payload...")
            agent_response = self.agent_callback_function(agent_invocation_prompt, event_payload)
            logger.info(f"Agent response: {agent_response}")

            # Notify all registered notification channels
            for notification_channel in self.notification_channels:
                try:
                    result = notification_channel.fire_notification(agent_response)
                    if not result:
                        logger.info(f"Failed to send notification to channel: {notification_channel.channel_name}")
                    else:
                        logger.info(f"Notification sent successfully to channel: {notification_channel.channel_name}")
                except Exception as e:
                    logger.error(f"Error notifying channel '{notification_channel.channel_name}': {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error processing ADS event: {e}", exc_info=True)

    def start(self):
        """
        Start the subscriber to listen for messages and process them.
        """
        if not self.data_connectors:
            raise ValueError("No data connectors provided.")
        
        for connector in self.data_connectors:
            # Launch a new thread for each connector to set up the callback and start listening on that thread
            data_connector_worker_thread = threading.Thread(target=connector.setup_callback, args=[self._socket_event_callback])
            data_connector_worker_thread.daemon = True  # Set as a daemon thread to exit when the main program exits
            data_connector_worker_thread.start()

        logger.info("All data connectors connected and callbacks set up.")
        logger.info("Subscriber started and listening for messages...")
        try:
            while True:
                # Keep the main thread alive to allow daemon threads to run and process messages from the job queue
                time.sleep(1)  # Sleep to prevent busy-waiting
                if len(self.ads_events_job_queue) > 0:
                    # Process the job queue in the main thread
                    current_event = self.ads_events_job_queue.pop(0)
                    self._process_ads_event_job_callback(current_event)
        except KeyboardInterrupt:
            self.stop()
            logger.debug("Subscriber stopped by user.")

    def stop(self):
        """
        Stop the subscriber and disconnect from all data connectors.
        """
        for connector in self.data_connectors:
            connector.ads_bridge_client.disconnect()
            logger.info(f"Disconnected from ADS Bridge for data connector: {connector.connector_name}")
        
        logger.info("Subscriber stopped and disconnected from all data connectors.")