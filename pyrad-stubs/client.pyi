from typing import Any

class Client:
    def __init__(
        self,
        server: str,
        secret: bytes,
        authport: int = 1812,
        dict: Any | None = None
    ) -> None: ...

    def CreateAuthPacket(self, code: int, User_Name: bytes) -> Any: ...

    def SendPacket(self, req: Any) -> Any: ...
