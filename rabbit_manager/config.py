from dataclasses import dataclass
from asyncio import AbstractEventLoop

@dataclass
class RabbitManagerConfig:
    host: str
    port: int
    username: str
    password: int
    loop: AbstractEventLoop
    heartbeat: int = 60
    retry_delay: int = 0
    connection_attempt: int = 2
    socket_timeout: int = 15