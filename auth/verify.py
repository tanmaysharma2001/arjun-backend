from fastapi import Header, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class Protected(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(Protected, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            Protected, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, id_token: str) -> bool:
        return id_token == "1234"
