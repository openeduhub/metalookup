
Topics:

- [Setup](setup.md)
- [Config](config.md)
- [Features](features.md)
- [Acceptance](acceptance.md)
- [Cache](cache.md)

# General

This service extracts metadata from a given URL.
It cannot yield answers regarding legal questions and issues or laws.
It requires iterative optimization and continuous maintenance due to th ever changing nature of URL content.

# Definition of Done:

- The service is able to perform with just the url of the website. No additional information is needed.
- The service performs its analysis in less than 30s, after about 120s of warm up, i.e., setup.
- The service is resilient against failing code, i.e., the user will always get a response.
  In the worst case, that response is an error message.


# Acceptance tests

To merge `dev` into `main` branch for release `dev` must:

- have all tests run successfully
- be able to build everything through `run.sh`. Sending a test request (e.g. with Postman) does return proper data.
- have running pre-commit hooks

All these must - currently, be executed manually, except for pre-commit hooks

# Exception handling

The service is split in two major pieces:
1. The API
2. The Manager

## The API

The API can be tested through docker healthchecks to `_ping`. If the API has failed, this endpoint will not react and
thus MetaLookup will be restarted

## The Manager

The manager logs exceptions partially to `docker logs` as well as `lib/logs/manager.log` due to the way `stdout` is used.
Exceptions can be grepped through the `ERROR` keyword.

Normally, each evaluation is handled separately, i.e., if evaluation fails, then exceptions are caught and at least a
reply with the exception traceback is given back to the API. Thus, even if the evaluation fails it only means an issue
for the respective evaluation, future evaluations are not impeded.

In the extreme case that an unhandled exception breaks the whole service, a global exception causes the service to
gracefully shutdown, logging the message `Unknown global exception`.
In that case, docker is configured to restart the service automatically. Currently running evaluations are aborted without
feedback, for now.
