
# 

# Testing REST

1. Start the container `run.sh`
2. Execute:
    ```shell script
    curl --location --request POST '0.0.0.0:5057/extract_meta' \
    --header 'Content-Type: application/json' \
    --data-raw '{"url": "here", "content": "cool_content123"}'
    ```
3. You should get
    ```shell script
   {"url":"here","meta":{"content_lenght":15}}%     
    ```