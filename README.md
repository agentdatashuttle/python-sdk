<!-- TODO -->

# Agent Data Shuttle (ADS) - Python SDK

#### Agent Data Shuttle (ADS) — _The framework that makes your AI agents autonomously react to external events._

> **ADS Python SDK** enables you to build ADS Publishers and Subscribers in Python, allowing your AI agents to react to external events in real time. It is interoperable with other ADS SDKs (NodeJS/TypeScript, n8n) and supports all publisher-subscriber combinations.

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
  - [n8n Integration](#3-n8n-integration)
- [Notification Channels](#notification-channels)
- [Types](#types)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

Agent Data Shuttle (ADS) is a framework for connecting event sources (publishers) and AI agents (subscribers) across platforms and languages. This SDK lets you build Python publishers and subscribers that can interoperate with NodeJS/TypeScript SDKs and n8n.

- **Publishers** send events (e.g., file uploads, system alerts, support tickets, CRM events, etc.).
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
- **n8n Integration:** Out-of-the-box support for n8n workflows as subscribers.
- **Notification Channels:** Send notifications via Email or Slack when agents process events.
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

![Architecture Diagram](https://raw.githubusercontent.com/your-org/your-repo/main/docs/architecture.png) <!-- TODO: Replace with your actual diagram if available -->

---

## Prerequisites

### Prerequisites for ADS Publisher

- **Python 3.8+**
- **RabbitMQ** instance (for event queueing and secure event publishing)
- **ADS Bridge** (for real-time event delivery via Socket.io).  
  You must run the ADS Bridge service which would be the point of connection for subscribers.
  More info at: [https://github.com/agentdatashuttle/ads-bridge](https://github.com/agentdatashuttle/ads-bridge)
- **Redis** (for handling ADS event delivery to a large number of ADS Subscribers from ADS Bridge)

### Prerequisites for ADS Subscriber

- **Python 3.8+**
- **Email/Slack credentials** (if using notification channels)
- **Redis** (for queuing ADS events and prevent overwhelmed agent invocations)
- **AI Agent or LLM** (for integrating with an AI model and trigger agentic workflows)

---

<!-- TODO -->

## Usage

### 1. ADS Publisher

Publish events to ADS subscribers.

```python
import os
import time
from agentdatashuttle_adspy.core.publisher import ADSPublisher
from agentdatashuttle_adspy.core.client import ADSClientParams
from agentdatashuttle_adspy.models.models import ADSDataPayload

client_params = ADSClientParams(
    host=os.getenv("ADS_HOST", "localhost"),
    username=os.getenv("ADS_USERNAME", "ads_user"),
    password=os.getenv("ADS_PASSWORD", "ads_password"),
    port=int(os.getenv("ADS_PORT", 5672))
)

publisher = ADSPublisher("UptimeKumaEvents", client_params)

payload = ADSDataPayload(
    event_name="container_down",
    event_description="the argocd service is down",
    event_data={
        "timestamp": "23-04-2004",
        "memory_captured_last": "2042Mi"
    }
)

time.sleep(2)  # Simulate some delay before publishing
publisher.publish_event(payload)
print("Event published successfully.")
```

**Tip:** Customize the event payload to match your use case, and provide a detailed `event_description` and as much detail as required in the `event_data` dictionary for the destination AI Agent to take remediation actions with greater confidence.

---

### 2. ADS Subscriber

Subscribe to events and invoke your AI agent.

```python
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from agentdatashuttle_adspy.core.subscriber import ADSSubscriber
from agentdatashuttle_adspy.core.dataconnector import ADSDataConnector
from agentdatashuttle_adspy.core.client import ADSBridgeClientParams
from agentdatashuttle_adspy.models.models import ADSDataPayload
from agentdatashuttle_adspy.core.notifications import EmailNotificationChannel, SlackNotificationChannel

# Define the tools for the agent to use
agent_tools = [toolA, toolB, see_k8s_logs_tool]
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

agent = create_react_agent(llm, agent_tools, debug=True)

def invoke_agent(prompt: str, payload: ADSDataPayload) -> str:
    print("The payload was:", payload)
    if payload.event_name == "container_up":
        return "NO INVOCATION FOR THIS EVENT - CONTAINER UP"
    response = agent.invoke({"messages": [HumanMessage(prompt)]})
    return response["messages"][-1].content

ads_bridge_client_params = ADSBridgeClientParams(
    connection_string="http://localhost:9999",
    path_prefix="/ads_bridge",
    ads_subscribers_pool_id="<a_random_uuid>"  # Replace with your actual pool ID to group horizontally scaled replicas of ADS Subscribers
)

data_connector_one = ADSDataConnector(
    connector_name="UptimeKumaConnector",
    bridge_client_params=ads_bridge_client_params
)

# Optionally, add notification channels
email_channel = EmailNotificationChannel(
    "Agent description",
    "smtp.example.com",
    587,
    "smtp_user",
    os.getenv("EMAIL_SMTP_PASSWORD", ""),
    "from@example.com",
    "to@example.com"
)

slack_channel = SlackNotificationChannel(
    "Agent description",
    os.getenv("SLACK_BOT_TOKEN", ""),
    "#your-channel"
)

ads_subscriber = ADSSubscriber(
    agent_callback_function=invoke_agent,
    llm=llm,
    agent_description="Agent description",
    data_connectors=[data_connector_one],
    notification_channels=[email_channel, slack_channel]
)

ads_subscriber.start()
```

---

<!-- TODO Decide Removal -->

### 3. n8n Integration

Use the n8n nodes provided in the [`via-rabbitmq/n8n/nodes`](via-rabbitmq/n8n/nodes) and [`via-bridge/n8n/nodes`](via-bridge/n8n/nodes) folders to integrate with n8n workflows.

---

<!-- TODO -->

## Notification Channels

Send notifications via Email or Slack when events are processed:

```python
from agentdatashuttle_adspy.core.notifications import EmailNotificationChannel, SlackNotificationChannel

email_channel = EmailNotificationChannel(
    "Agent description",
    "smtp.example.com",
    587,
    "smtp_user",
    "smtp_pass",
    "from@example.com",
    "to@example.com"
)

slack_channel = SlackNotificationChannel(
    "Agent description",
    "xoxb-your-slack-bot-token",
    "#your-channel"
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
[agentdatashuttle@knowyours.co](mailto:agentdatashuttle@knowyours.co) or [sudhay2001@gmail.com](mailto:sudhay2001@gmail.com)

For more information about Agent Data Shuttle - https://agentdatashuttle.knowyours.co
