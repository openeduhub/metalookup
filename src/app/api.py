from fastapi import FastAPI
from pydantic import BaseModel

import manager

app = FastAPI()


class Input(BaseModel):
    url: str
    content: str
    result: dict


class Output(BaseModel):
    url: str
    meta: dict


@app.post('/extract_meta')
def extract_meta(request: Input):
    main_extractor = manager.Manager()

    main_extractor.setup()
    result = main_extractor.start(html_content=Input.url)

    out = Output(url=request.url, meta={"content_lenght": len(result), "result": result})

    return out
