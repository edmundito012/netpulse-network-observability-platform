from abc import ABC
from abc import abstractmethod


class BaseNotificationProvider(ABC):

    @abstractmethod
    def send(
        self,
        title: str,
        body: str,
    ) -> bool:
        pass