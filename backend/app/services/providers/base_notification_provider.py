from abc import ABC, abstractmethod


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(
        self,
        title: str,
        body: str,
    ) -> bool:
        pass
