import logging
from abc import ABC, abstractmethod
from utils.models import Message



LOGGER = logging.getLogger(__name__)


class MessageFactory:
    def get_engine(self, engine: str):
        if engine == "logger":
            return LoggerMessaging()
        elif engine == "mqtt":
            LOGGER.error(f"The engine {engine} has not yet been implemented.")
            raise NotImplementedError
        elif engine == "http":
            LOGGER.error(f"The engine {engine} has not yet been implemented.")
            raise NotImplementedError
        elif engine == "amqp":
            LOGGER.error(f"The engine {engine} has not yet been implemented.")
            raise NotImplementedError
        else:
            LOGGER.error(f"The engine {engine} has not yet been implemented.")
            raise NotImplementedError


class Engine(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def publish(self, message: Message):
        pass


class LoggerMessaging(Engine):
    def publish(self, message: Message):
        LOGGER.info(f"Message = {message}")
