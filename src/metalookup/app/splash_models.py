from pydantic import BaseModel, HttpUrl


class Header(BaseModel):
    """
    A single key value header pair.
    See also http://www.softwareishard.com/blog/har-12-spec/#headers
    """

    name: str
    value: str


class Cookie(BaseModel):
    """
    A single cookie of a request or response.
    See also http://www.softwareishard.com/blog/har-12-spec/#cookies
    """

    name: str
    value: str
    httpOnly: bool
    secure: bool


class Response(BaseModel):
    """
    A recorded response for a given request.
    See also http://www.softwareishard.com/blog/har-12-spec/#response
    """

    headers: list[Header]
    cookies: list[Cookie]
    status: int  # the HTTP response code


class Request(BaseModel):
    """
    A request that was issued by splash.
    See also http://www.softwareishard.com/blog/har-12-spec/#request
    """

    url: HttpUrl
    method: str
    headers: list[Header]
    cookies: list[Cookie]


class Entry(BaseModel):
    """
    A single entry of the HAR Log.
    See also http://www.softwareishard.com/blog/har-12-spec/#entries
    """

    response: Response
    request: Request


class Log(BaseModel):
    """
    The root of exported data.
    See also http://www.softwareishard.com/blog/har-12-spec/#log
    """

    entries: list[Entry]


class HAR(BaseModel):
    """Splash specific container for the HAR log."""

    log: Log


class SplashResponse(BaseModel):
    """
    The response received from a splash render-html request.

    Not all fields received in the response are listed here for now. However, what is listed here is required.
    """

    url: HttpUrl
    html: str
    har: HAR
