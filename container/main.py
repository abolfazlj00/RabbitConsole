from dependency_injector.containers import DeclarativeContainer
from dependency_injector import providers


class MainContainer(DeclarativeContainer):
    config = providers.Configuration()

    rabbit_manager = providers.Singleton(
        
    )