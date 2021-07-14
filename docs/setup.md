
# Install

You will need poetry and python3.9.1:

`sudo apt-get install python3.9`     
`python3.9 -m pip3 install poetry`

# Staying up to date

The repository and docker containers do not auto update.
Update the dependencies and rebuild the containers regularly.

## CI Pipeline

WIP

# Launching the container

1. Start the containers by executing `run.sh` from the main folder, not from `src`
2. The main container can be reached on `http://0.0.0.0:5057`

# Accessing the Swagger UI

The Swagger UI of FastApi can be access by:

- `http://0.0.0.0:5057/redoc`
- or alternatively `http://0.0.0.0:5057/doc`

# Testing REST

1. Start the container
2. Execute:
   
    ```
    curl --location --request POST '0.0.0.0:5057/extract_meta' \
    --header 'Content-Type: application/json' \
    --data-raw '{"url": "here", "html": "cool_content123", "headers": ""}'
    ```
   
3. You should get
   
    ```
   {"url":"here","meta":{...}}     
    ```

# Pre commit

To see tracebacks of why the pre commit hook fails run in terminal:

```
pre-commit run --all-files 
```


# Tests

Tests are divided into three categories:

- End-To-End (E2E)
- Integration
- Unit

The E2E test comprises a test with minimum input but maximum coverage.
Basically, every part of the program and any connected containers are used.
Due to its time requirements, it is currently skipped, but could be included, e.g., in Github Actions

Currently not covered by tests yet

- rester.py
- evaluator.py

since these scripts are used by DevOps only and not needed for production.