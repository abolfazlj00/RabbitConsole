from rabbit_manager import RabbitManagerConfig, RabbitManager, RabbitMQPermission, check_permission
from rabbit_manager.main import ConnectionState
from typing import Dict
from decouple import config

HOST:str=config("HOST")
PORT:int=config("PORT")

from bclib import edge

options = {
    "server": "localhost:8080",
    "router": {
        "restful": ["/api"],
        "web": ["*"]
    }
}

app = edge.from_options(options)

users: Dict[str, RabbitManager] = {}

@app.restful_action(
    app.post("api/login")
)
def process_login(context: edge.RESTfulContext):
    try:
        try:
            body = context.body
            if body is None:
                raise
            username = body.username
            if username is None:
                raise
            password = body.password
            if password is None:
                raise
        except:
            raise edge.BadRequestErr(data={"error": "invalid data"})
        loop = context.dispatcher.event_loop
        manager = RabbitManager(
            RabbitManagerConfig(
                host=HOST,
                port=PORT,
                username=username,
                password=password,
                loop=loop
            )
        )
        loop.run_in_executor(
            None, manager.initialize
        )
        users[manager.id] = manager
        content = {
            "id": manager.id
        }
    except edge.ShortCircuitErr as ex:
        # print(ex)
        context.status_code = ex.status_code
        content = ex.data
    except Exception as ex:
        print(repr(ex))
        context.status_code = edge.HttpStatusCodes.INTERNAL_SERVER_ERROR
        content = {
            "Error": "Server Error"
        }
    return content

@app.restful_action(
    app.get("api/exchanges/:id")
)
async def process_connection_exchanges(context: edge.RESTfulContext):
    try:
        manager_id = context.url_segments.id
        manager = users.get(manager_id)
        if manager is None:
            raise edge.BadRequestErr(data={"Error": "Invalid id"})
        check_permission(manager, RabbitMQPermission.EXCHANGE_READ)
        content = await manager.get_exchanges_async()
    except edge.ShortCircuitErr as ex:
        # print(ex)
        context.status_code = ex.status_code
        content = ex.data
    except Exception as ex:
        print(repr(ex))
        context.status_code = edge.HttpStatusCodes.INTERNAL_SERVER_ERROR
        content = {
            "Error": "Server Error"
        }
    return content

@app.restful_action(
    app.get("api/queues/:id")
)
async def process_connection_queues(context: edge.RESTfulContext):
    try:
        manager_id = context.url_segments.id
        manager = users.get(manager_id)
        if manager is None:
            raise edge.BadRequestErr(data={"Error": "Invalid id"})
        check_permission(manager, RabbitMQPermission.QUEUE_READ)
        content = await manager.get_queues_async()
    except edge.ShortCircuitErr as ex:
        # print(ex)
        context.status_code = ex.status_code
        content = ex.data
    except Exception as ex:
        print(repr(ex))
        context.status_code = edge.HttpStatusCodes.INTERNAL_SERVER_ERROR
        content = {
            "Error": "Server Error"
        }
    return content

@app.restful_action(
    app.get("api/status/:id")
)
def process_conenction_status(context: edge.RESTfulContext):
    try:
        manager_id = context.url_segments.id
        if manager_id not in users:
            raise edge.BadRequestErr(data={"Error": "Invalid id"})
        content = {
            "conenctionStatus": users[manager_id].conenction_state.value
        }
    except edge.ShortCircuitErr as ex:
        # print(ex)
        context.status_code = ex.status_code
        content = ex.data
    except Exception as ex:
        print(repr(ex))
        context.status_code = edge.HttpStatusCodes.INTERNAL_SERVER_ERROR
        content = {
            "Error": "Server Error"
        }
    return content


app.listening()