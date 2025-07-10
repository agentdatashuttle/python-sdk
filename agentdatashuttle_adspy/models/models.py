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
    ads_subscribers_pool_id: str

    def __init__(self, connection_string: str, path_prefix: str, ads_subscribers_pool_id: str):
        self.connection_string = connection_string
        self.path_prefix = path_prefix

        if(not ads_subscribers_pool_id or ads_subscribers_pool_id == ""):
            raise ValueError("'ads_subscribers_pool_id' cannot be empty or None")
        
        self.ads_subscribers_pool_id = ads_subscribers_pool_id

class RedisParams:
    host: str
    port: int

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port