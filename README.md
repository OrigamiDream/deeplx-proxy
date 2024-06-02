# DeepLX Proxy

DeepLX with weighted proxy Load balancing supports

## Usage
```
docker pull acaciastech/deeplx-proxy:1.0.0
docker run --name deeplx-proxy -p 1188:1188 --rm -v $(pwd)/proxies:/data acaciastech/deeplx-proxy:1.0.0
```

```http request
POST http://localhost:1188/translate
Content-Type: application/json

{
  "text": "Hello World!",
  "source_lang": "EN",
  "target_lang": "KO",
  "max_retry": -1,
  "num_proxies": 5
}
```

## License

Licensed under the [MIT license](https://github.com/OrigamiDream/deeplx-proxy/blob/main/LICENSE).
