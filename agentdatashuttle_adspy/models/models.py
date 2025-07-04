from pydantic import BaseModel

class ADSDataPayload(BaseModel):
    event_name: str
    event_description: str
    event_data: dict

class ADSRabbitMQClientParams:
    host: str
    port: int
    username: str
    password: str

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

class ADSBridgeClientParams:
    connection_string: str
    path_prefix: str

    def __init__(self, connection_string: str, path_prefix: str):
        self.connection_string = connection_string
        self.path_prefix = path_prefix

class RedisParams:
    host: str
    port: int

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port