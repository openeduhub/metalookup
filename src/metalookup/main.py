from metalookup.lib.settings import API_PORT, LOG_LEVEL


def main():
    import uvicorn

    uvicorn.run("metalookup.app.api:app", host="0.0.0.0", port=API_PORT, log_level=LOG_LEVEL)


if __name__ == "__main__":
    main()
