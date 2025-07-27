# Agent Data Shuttle (ADS) - Python SDK

#### Agent Data Shuttle (ADS) — _The framework that makes your AI agents autonomously react to external events._

> **ADS Python SDK** enables you to build ADS Publishers and Subscribers in Python, allowing your AI agents to react to external events in real time.

> It is interoperable with other ADS SDKs (NodeJS/TypeScript, n8n) and supports all publisher-subscriber combinations.

---

## Installation

```sh
pip install agentdatashuttle_adspy
```

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
  - [ADS Publisher](#1-ads-publisher)
  - [ADS Subscriber](#2-ads-subscriber)
- [Notification Channels](#notification-channels)
- [Types](#types)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

Agent Data Shuttle (ADS) is a framework for connecting event sources (publishers) and AI agents (subscribers) across platforms and languages.

This SDK lets you build Python publishers and subscribers that can interoperate with NodeJS/TypeScript SDKs and n8n.

- **Publishers** send events (e.g., file uploads, system alerts, support tickets, CRM events, payment processor events, etc.).
- **Subscribers** (AI agents or workflows) receive and react to those events to take appropriate actions.

All combinations are possible:

- Python Publisher → Python Subscriber
- Python Publisher → NodeJS Subscriber
- Python Publisher → n8n Subscriber
- NodeJS Publisher → Python Subscriber
- NodeJS Publisher → n8n Subscriber
- NodeJS Publisher → NodeJS Subscriber
- n8n Publisher → Python Subscriber
- n8n Publisher → NodeJS Subscriber
- n8n Publisher → n8n Subscriber

---

## Features

- **Event-Driven Architecture:** Publish and subscribe to events between systems and agents.
- **Publisher & Subscriber SDKs:** Build both event sources (publishers) and event consumers (subscribers) in Python.
- **n8n Integration:** Out-of-the-box support for n8n workflows as subscribers or publishers.
- **Notification Channels:** Send notifications via Email or Slack when agents process events.
  > More channels coming soon.
- **Pluggable Connectors:** Connect an ADS Subscriber to multiple ADS Publishers via data connectors.
- **Prompt Generation:** Automatically generate contextual prompts for AI agents based on event payloads and agent capabilities.
- **Type Hints:** Strong typing for safer and more maintainable code.

---

## Architecture

- **ADS Publisher:** Sends events to subscribers via ADS Bridge.
- **ADS Bridge:** (see [ADS Bridge repository](https://github.com/agentdatashuttle/ads-bridge)) Broadcasts events to connected subscribers.
- **ADS Subscriber:** Receives ADS events and invokes AI agents or workflows.
- **Notification Channels:** Email/Slack notifications on event processing.
- **Interoperability:** Mix Python, NodeJS, and n8n publishers/subscribers.

> ![Before and After ADS](https://agentdatashuttle.knowyours.co/before-after-illustration.png)
>
> ![Architecture Diagram](https://agentdatashuttle.knowyours.co/architecture-diagram.png)

---

## Prerequisites

### Prerequisites for ADS Publisher

- **Python 3.8+**

- **RabbitMQ** instance

  > For event queueing and secure event publishing

- **ADS Bridge**

  > For real-time event delivery via Socket.io
  >
  > You must run the ADS Bridge service which would be the point of connection for subscribers.
  >
  > More info at: [https://github.com/agentdatashuttle/ads-bridge](https://github.com/agentdatashuttle/ads-bridge)

- **Redis**

  > For handling ADS event delivery to a large number of ADS Subscribers from ADS Bridge

### Prerequisites for ADS Subscriber

- **Python 3.8+**

- **Email/Slack credentials** (Optional)

  > For using notification channels upon each autonomous agent invocation

- **AI Agent or LLM** (for integrating with an AI model and trigger agentic workflows)

---

## Usage

### 1. ADS Publisher

Publish events to ADS subscribers.

```python
import os
import time
from agentdatashuttle_adspy.core.client import ADSRabbitMQClientParams
from agentdatashuttle_adspy.core.publisher import ADSPublisher
from agentdatashuttle_adspy.models.models import ADSDataPayload

# Step 1: Create ADSRabbitMQClientParams
client_params = ADSRabbitMQClientParams(
                    host=os.getenv("RABBITMQ_HOST", "localhost"),
                    username=os.getenv("RABBITMQ_USERNAME", "ads_user"),
                    password=os.getenv("RABBITMQ_PASSWORD", "ads_password"),
                    port=int(os.getenv("RABBITMQ_PORT", 5672))
                )


# Step 2: Create a ADSPublisher instance
# Example: ADSPublisher for Kubernetes Health monitoring system
publisher = ADSPublisher("KubernetesMonitoring", client_params)

# Step 3: Create a sample ADSDataPayload
payload = ADSDataPayload(
    event_name="pod_killed",
    event_description="Pod 'payment-service-233ch3' just got killed due to OOMKilled error",
    event_data={
        "pod": "payment-service-233ch3",
        "recorded_memory_usage": "2042Mi",
        "limits": "2000Mi"
    }
)

time.sleep(2)  # Simulate some delay before publishing

# Publish the payload
publisher.publish_event(payload)

print("Event published successfully.")
```

**Tip:** Customize the event payload to match your use case, and provide a detailed `event_description` and as much detail as required in the `event_data` dictionary for the subscriber AI Agent to take remediation actions with greater confidence and accuracy.

---

### 2. ADS Subscriber

Subscribe to events and invoke your AI agent.

```python
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import ADS Subscriber and add ADS Data Connectors
from agentdatashuttle_adspy.core.subscriber import ADSSubscriber
from agentdatashuttle_adspy.core.dataconnector import ADSDataConnector
from agentdatashuttle_adspy.core.client import ADSBridgeClientParams
from agentdatashuttle_adspy.models.models import ADSDataPayload
from agentdatashuttle_adspy.core.notifications import EmailNotificationChannel, SlackNotificationChannel

# Define the tools for the agent to use
agent_tools = [toolA, toolB, see_k8s_logs_tool]
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

agent = create_react_agent(llm, agent_tools, debug=True)

# Step 1: Define callback function for ADS Subscriber to invoke agent
def invoke_agent(prompt: str, payload: ADSDataPayload) -> str:
    print("The ADS payload was:", payload)

    # Filter specific events in/out as you desire
    if payload.event_name == "container_up":
        return "NO AGENT INVOCATION FOR THIS EVENT - CONTAINER UP"

    # Invoke your agent with the context enriched prompt generated by Agent Data Shuttle
    response = agent.invoke({"messages": [HumanMessage(prompt)]})

    # Return final agent response - will be sent to all notification channels for later review
    return response["messages"][-1].content

# Step 2: Define ADSBridgeClientParams and corresponding ADSDataConnector
ads_bridge_client_params = ADSBridgeClientParams(
    connection_string="http://localhost:9999",
    path_prefix="/ads_bridge",
    ads_subscribers_pool_id="<a_random_uuid>"  # Replace with your actual pool ID to group horizontally scaled replicas of ADS Subscribers - use https://agentdatashuttle.knowyours.co/pool-id-generator to make one if needed
)

data_connector_one = ADSDataConnector(
    connector_name="K8sMonitoringConnector",
    bridge_client_params=ads_bridge_client_params
)

# Step 3: Optionally, add notification channels
email_channel = EmailNotificationChannel(
    "<agent_description>",
    "<smtp_host>",
    "<smtp_port>",
    "<smtp_username>",
    "<smtp_password>",
    "from@example.com",
    "to@example.com"
)

slack_channel = SlackNotificationChannel(
    "<agent_description>",
    "<slack_bot_token>",
    "#<your-channel>"
)

# Step 4: Create the ADSSubscriber with the callback function, LLM, and Data Connectors.
# The ADSSubscriber will listen for events from all the data connectors and invoke the agent.
ads_subscriber = ADSSubscriber(
    agent_callback_function=invoke_agent,
    llm=llm,
    agent_description="<agent_description>",
    data_connectors=[data_connector_one],
    notification_channels=[email_channel, slack_channel]
)

# Step 5: Start the ADSSubscriber to listen for events and invoke the agent.
ads_subscriber.start()
```

---

## Notification Channels

Send notifications via Email or Slack when events are processed:

```python
from agentdatashuttle_adspy.core.notifications import EmailNotificationChannel, SlackNotificationChannel

email_channel = EmailNotificationChannel(
    "<agent_description>",
    "<smtp_host>",
    "<smtp_port>",
    "<smtp_username>",
    "<smtp_password>",
    "from@example.com",
    "to@example.com"
)

slack_channel = SlackNotificationChannel(
    "<agent_description>",
    "<slack_bot_token>",
    "#<your-channel>"
)
```

Pass these channels to the `ADSSubscriber` to enable notifications.

---

## Types

All core types are defined in [`agentdatashuttle_adspy/models/models.py`](agentdatashuttle_adspy/models/models.py):

- [`ADSDataPayload`](agentdatashuttle_adspy/models/models.py)
- [`ADSClientParams`](agentdatashuttle_adspy/core/client.py)
- [`ADSBridgeClientParams`](agentdatashuttle_adspy/core/client.py)

---

## Logging

Logging level can be configured via the `LOG_LEVEL` environment variable with the following values:

| Level | Description                                     |
| ----- | ----------------------------------------------- |
| error | Critical errors that may cause the app to crash |
| warn  | Warnings about potentially harmful situations   |
| info  | General operational information                 |
| debug | Debug-level logs for development                |

---

## Contributing

Contributions are welcome!

If you have ideas for improvements, bug fixes, or new features, please open a [GitHub Issue](https://github.com/agentdatashuttle/python-sdk/issues) to discuss or submit a Pull Request (PR).

**How to contribute:**

1. Fork this repository and create your branch from `main`.
2. Make your changes with clear commit messages.
3. Ensure your code passes tests.
4. Open a Pull Request describing your changes.

If you encounter any bugs or have feature requests, please [raise an issue](https://github.com/agentdatashuttle/python-sdk/issues) on GitHub.

Thank you for helping improve the Agent Data Shuttle initiative!

---

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

---

## Contact

For questions or support, please contact  
[agentdatashuttle@knowyours.co](mailto:agentdatashuttle@knowyours.co)

For more information about Agent Data Shuttle - https://agentdatashuttle.knowyours.co
