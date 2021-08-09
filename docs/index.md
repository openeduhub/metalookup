
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
