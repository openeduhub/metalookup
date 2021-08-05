
Topics:

- [Setup](setup.md)
- [Config](config.md)
- [Features](features.md)
- [Acceptance](acceptance.md)
as
# Definition of Done:

- The service is able to perform with just the url of the website. No additional information is needed.
- The service performs its analysis in less than 30s, especially for the first call directly after container launch
- The service is resilient against failing code, i.e., the user will always get a response.
  In the worst case, that response is an error message.


# Acceptance tests

To merge `main` into `prod` branch for release `main` must:

- have all tests run successfully
- be able to build everything through `run.sh`. Sending a test request (e.g. with Postman) does return proper data.
- have running pre-commit hooks

All these must - currently, be executed manually, except for pre-commit hooks
