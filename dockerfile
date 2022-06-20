FROM python:3.9-slim

RUN adduser --system extractor

WORKDIR /home/extractor

# make wheel file built with poetry build available in docker build step
COPY ./*.whl /home/extractor

# install the wheel file and all its (transitive) dependencies. We install directly into
# the system python environment.
RUN pip install --no-cache-dir /home/extractor/*.whl

USER extractor

# execute the entrypoint defined in pyproject.toml
CMD meta-lookup
