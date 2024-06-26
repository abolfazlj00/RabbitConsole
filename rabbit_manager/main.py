from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika import ConnectionParameters, PlainCredentials
from rabbit_manager.config import RabbitManagerConfig
from enum import Enum
from dataclasses import dataclass
import uuid
import asyncio
import aiohttp

@dataclass
class Response:
    status: int
    json: any
    reason: str

class ConnectionState(Enum):
    CLOSED = "closed"
    INIT = "init"
    PROTOCOL = "protocol"
    START = "start"
    TUNE = "tune"
    OPEN = "open"
    CLOSING = "closing"

class RabbitManager:
    MAX_RECONNECTION_TIMES = 5
    MAX_RECONNECTION_DELAY = 30 # seconds
    STATES = {
        AsyncioConnection.CONNECTION_CLOSED: ConnectionState.CLOSED,
        AsyncioConnection.CONNECTION_INIT: ConnectionState.INIT,
        AsyncioConnection.CONNECTION_PROTOCOL: ConnectionState.PROTOCOL,
        AsyncioConnection.CONNECTION_START: ConnectionState.START,
        AsyncioConnection.CONNECTION_TUNE: ConnectionState.TUNE,
        AsyncioConnection.CONNECTION_OPEN: ConnectionState.OPEN,
        AsyncioConnection.CONNECTION_CLOSING: ConnectionState.CLOSING
    }


    def __init__(self, config: RabbitManagerConfig) -> None:
        self.__config = config
        self.__loop = self.__config.loop
        self.__params = ConnectionParameters(
            host=self.__config.host,
            port=self.__config.port,
            credentials=PlainCredentials(
                username=self.__config.username,
                password=self.__config.password
            ),
            heartbeat=self.__config.heartbeat,
            connection_attempts=self.__config.connection_attempt,
            retry_delay=self.__config.retry_delay,
            socket_timeout=self.__config.socket_timeout
        )
        self.__debug = False
        self.__uniqueId = uuid.uuid4()
        self.__connection: AsyncioConnection = None
        self.__channel: Channel = None
        self.__reconnect_times = 0
        self.__reconnect_delay = 0

    def __print(self, msg: any):
        print(f"[{self.__uniqueId}]", msg)

    def __print_exception(self, exception: BaseException, force_print: bool=False):
        if self.__debug or force_print:
            self.__print(f"[{exception.__class__.__name__}] {repr(exception)}")

    def initialize(self):
        self.__connection = AsyncioConnection(
            parameters=self.__params,
            on_open_callback=self.__on_connection_open,
            on_open_error_callback=self.__on_open_conenction_error,
            on_close_callback=self.__on_close_connection,
            custom_ioloop=self.__loop
        )

    def __on_connection_open(self, connection: AsyncioConnection):
        self.__print("conenction opened.")
        self.__channel = connection.channel(
            on_open_callback=self.__on_open_channel
        )

    def __on_close_connection(self, connection: AsyncioConnection, exception: BaseException):
        self.__print("connection closed.")
        self.__print_exception(exception)

        self.__channel = None
        if RabbitManager.MAX_RECONNECTION_TIMES == 0 or self.__reconnect_times <= RabbitManager.MAX_RECONNECTION_TIMES:
            self.__loop.create_task(
                self.__try_to_reconenct_async()
            )

    def __get_reconnect_delay(self):
        self.__reconnect_delay = min(self.__reconnect_delay + 1, RabbitManager.MAX_RECONNECTION_DELAY)
        return self.__reconnect_delay

    async def __try_to_reconenct_async(self):
        connection_delay = self.__get_reconnect_delay()
        self.__print(f"Reconnecting in {connection_delay} seconds.")
        await asyncio.sleep(connection_delay)
        self.__reconnect_delay += 1
        self.initialize()

    def __on_open_conenction_error(self, connection: AsyncioConnection, exception):
        self.__print("connection failed.")
        self.__print_exception(exception)

    def __on_open_channel(self, channel: Channel):
        self.__print("channel opened.")

    @property
    def id(self):
        return str(self.__uniqueId)

    @property
    def conenction_state(self):
        if self.__connection is None:
            raise ValueError('manager not initialized')
        conn_state = RabbitManager.STATES.get(self.__connection.connection_state)
        if conn_state is None:
            raise NotImplementedError(
                f'stete {self.__connection.connection_state} not defined'
            )
        return conn_state 

    @property
    def channel_info(self):
        if self.__channel is None:
            raise ValueError('there is not any available channel')
        print(f'''
    Callbacks: {self.__channel.callbacks}
    Channel-Number: {self.__channel.channel_number}
    Flow-Active: {self.__channel.flow_active}
    Consumer-Tags: {self.__channel.consumer_tags}
        ''')
    

    async def get_request_async(self, segment_url: str):
        url = f'http://{self.__params.host}:15672/{segment_url}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=aiohttp.BasicAuth(self.__config.username, self.__config.password)) as response:
                return Response(
                    response.status,
                    await response.json(encoding="utf-8"),
                    response.reason
                )
                

    async def get_exchanges_async(self):
        response = await self.get_request_async(segment_url='api/exchanges')
        if response.status == 200:
            exchanges = response.json
            return [
                {
                    "Name": exchange['name'],
                    "Type": exchange['type'],
                    "Vhost": exchange['vhost'],
                }
                for exchange in exchanges
            ]
        else:
            print(f"Failed to get exchanges: {response.status} - {response.reason}")

    async def get_queues_async(self):
        response = await self.get_request_async(segment_url='api/queues')
        if response.status == 200:
            queues = response.json
            return [
                {
                    "Name": queue['name'],
                    "Messages": queue['messages'],
                    "Vhost": queue['vhost'],
                }
                for queue in queues
            ]
        else:
            print(f"Failed to get exchanges: {response.status} - {response.reason}")