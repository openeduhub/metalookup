# Meta-Data extraction with MetaLookup
The _MetaLookup_ service extracts and suggests metadata related to OER from a given URL. To achieve this, it
uses the [Playwright](https://playwright.dev/) [python package](https://pypi.org/project/playwright/) to fetch the
content of the URL and then analyzes the issued requests and responses and the final rendered HTML document. It further
uses [Lighthouse](https://github.com/GoogleChrome/lighthouse) to assess the accessibility of the content.
It requires iterative optimization and continuous maintenance due to the ever-changing nature of URL content.

## Feature Documentation
The documentation regarding which metadata fields are extracted and how they can be found [here](./docs/features.md) and
[here](./docs/acceptance.md). It can be rendered as HTML with the following command:
```bash
mkdocs serve
```
The different extractors are implemented [here](./src/metalookup/features).

## Local Setup
MetaLookup requires python 3.9 or later and [poetry](https://python-poetry.org/docs/#installation). To test the
application without mocking external services, [docker](https://www.docker.com/) is required as well.

With poetry installed running the following commands will set up a poetry environment and install application and
development dependencies.
```bash
poetry env use 3.9
poetry install
```

## Code Style & Pre-commit hook
The code style is enforced via tools configured in [.pre-commit-config.yaml](./.pre-commit-config.yaml) and
[pyproject.toml](./pyproject.toml). After setting up the environment (which will install the python
`pre-commit` script) one should install the hook via:
```bash
pre-commit install
```
This will make sure that the commits follow the defined codestyle and the respective CI pipeline step will pass.

## Unit-Tests
Unit-tests are divided into two categories:

- Application tests: These tests make sure, the application functions properly.
- Extractor tests: These tests test the individual feature generation units.

All tests make use of mocks and static (checked in) resources. Hence, they can run independently of any docker
container or other environment constraints.

## Branching Model
This repository follows the [GitHub Flow](http://scottchacon.com/2011/08/31/github-flow.html) branching model:

> - Anything in the main branch is deployable
> - To work on something new, create a descriptively named branch off of master (ie: new-oauth2-scopes)
> - Commit to that branch locally and regularly push your work to the same named branch on the server
> - When you need feedback or help, or you think the branch is ready for merging, open a pull request
> - After someone else has reviewed and signed off on the feature, you can merge it into main
> - Once it is merged and pushed to ‘main’, you can and should deploy immediately

## Definition of Done
- The service is able to perform with just the url of the website. No additional information is needed.
- The service is resilient against failing code, i.e., the user will never get a "500 Internal Server Error".
  In the worst case, that response is an error message.
- CI Pipeline passes (Unit tests, pre-commit, and build steps)

## CI Pipeline
The pipeline is launched by creating or updating a branch and has to succeed before any pull request can be merged.
It will perform the following steps:
 - run pre-commit hooks to validate codestyle and quality
 - build python package
 - run python unittests
 - build docker images
 - (on main branch) push docker images to registry.

## Releases & Versioning
- This repository uses [Sem-Ver](https://semver.org/lang/de/).
TODO: https://github.com/openeduhub/metalookup/issues/150
- New releases are created via the GitHub release interface.
- Release Tags must follow the pattern `v{MAJOR}.{MINOR}.{PATCH}`
- Docker tags will be extracted from the git tags as `{MAJOR}.{MINOR}.{PATCH}`

## Deployment
MetaLookup requires Playwright and Lighthouse containers to be running. To deploy them together the two docker-compose files
for [dev](./meta-lookup-compose-dev.yml) and [prod](./meta-lookup-compose-prod.yml) are used. These dockerfiles also
contain the configuration to run MetaLookup with a persistent cache via a postgres container.

### Extractor Container (custom image)
This container contains the main API and implementation of MetaLookup. Other services should only communicate with this
container, the other containers are considered internal and should not be exposed to the outside world.

### Playwright Container (`browserless/chrome` image)
Playwright is a toolkit that allows to remote-control a browser. We here use the
[browserless/chrome](https://hub.docker.com/r/browserless/chrome) image which essentially provides "chrome as a
service" to which MetaLookup talks with the [playwright python package](https://pypi.org/project/playwright/) via a
websocket.

### Lighthouse Container (custom image)
Lighthouse is a software tool that analyses accessibility of a website. This repository contains a custom dockerfile
where this tool is packaged together with a browser
([google-chrome-headless image](https://hub.docker.com/r/femtopixel/google-chrome-headless)). Here the accessibility
command line tool is provided via a [minimal custom-made HTTP API](./src/app/api.py).

### Postgres Container (optional, official `postgres` image)
The postgres container provides a way to persist cache for the Extractor container. It is optional, as caching can
also be done via sqlite (for a single instance of MetaLookup) or completely disabled. Alternatively a dedicated other
postgres database can be used and configured. See [settings.py](./src/metalookup/lib/settings.py).

## Configuration
The application can be configured via environment variables or a `.env` file. See
[`settings.py`](./src/metalookup/lib/settings.py) for the available options.

## Health-Checks
The service provides a `/_ping` endpoint which will respond with a `200 OK` (body: `{"status": "ok"}`) immediately
(within a couple of milliseconds). If the request takes to long, or answers differently, then the service is in an
inconsistent state and should be restarted. This endpoint is also configured in the docker-compose to be used for
health checks of the docker daemon to trigger automated restarts in case of unhealthy containers.

## Testing with `curl`
When the container is running, the endpoints can be tested e.g. with `curl`:
 ```bash
 curl --location --request POST 'localhost:{your-port}/extract' \
 --header 'Content-Type: application/json' \
 --data-raw '{"url": "https://some-domain.org/index.html"}'
 ```
See the files [api.py](./src/metalookup/app/api.py) and [models.py](./src/metalookup/app/models.py) for the API and
model documentation, or alternatively visit the [Swagger-UI](http://localhost:5057/docs) of the locally running service.
