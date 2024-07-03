from fastapi import Request
from contextlib import contextmanager

from backend.app.database.models.request import RequestLog
from backend.app.database.instance import get_session

class RequestLogRepository:
    def __init__(self, session):
        self.session = session

    async def create_log(self, request: Request):
        body = await request.body()
        log = RequestLog(
            relo_method=request.method,
            relo_url=str(request.url),
            relo_headers=dict(request.headers),
            relo_query_params=dict(request.query_params),
            relo_client_host=request.client.host,
            relo_client_port=request.client.port,
            relo_cookies=dict(request.cookies),
            relo_body=body.decode("utf-8") if body else None
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

@contextmanager
def get_request_log_repository():
    with get_session() as session:
        yield RequestLogRepository(session)
