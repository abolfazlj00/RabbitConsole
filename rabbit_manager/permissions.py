from enum import Enum
from rabbit_manager.main import RabbitManager
from bclib.edge import ForbiddenErr

class RabbitMQPermission(Enum):
    EXCHANGE_CREATE = "EXCHANGE_CREATE"
    EXCHANGE_READ = "EXCHANGE_READ"
    EXCHANGE_UPDATE = "EXCHANGE_UPDATE"
    EXCHANGE_DELETE = "EXCHANGE_DELETE"
    QUEUE_CREATE = "QUEUE_CREATE"
    QUEUE_READ = "QUEUE_READ"
    QUEUE_UPDATE = "QUEUE_UPDATE"
    QUEUE_DELETE = "QUEUE_DELETE"

def check_permission(manager: RabbitManager, operator: RabbitMQPermission):
    return True
    raise ForbiddenErr(data={"Error": "Access is denied"})