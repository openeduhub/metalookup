This directory contains splash responses (and the respective HAR) that can be obtained with the splash docker container.
To generate additional sample data the docker container can be started with:#

```bash
docker run -p 8050:8050  scrapinghub/splash:latest
```

Then
 - visit [the splash ui](http://0.0.0.0:8050/)
 - fill out the target URL text box
 - click on render
 - download har and html and save them to a new sampe json file.
