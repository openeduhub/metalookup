from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Input(BaseModel):
    url: str
    content: str


class Output(BaseModel):
    url: str
    meta: dict


@app.post('/extract_meta')
def extract_meta(request: Input):
    out = Output(url=request.url, meta={"content_lenght": len(request.content)})

    return out
