# Description of yapi

It allows to use declarative language (yaml) to talk to APIs and to save the response for future ones.

The main use case is to talk to [HashiCorp Vault API](https://www.vaultproject.io/api/overview.html).

It is heavily based on [Tavern-ci](https://github.com/taverntesting/tavern)
# How to use it
For this example we will use `http://httpbin.org/put` as `VAULT_ADDR`, this service will echo everything we send plus extra information about our request.

```c
$ export VAULT_ADDR=http://httpbin.org/put
$ export VAULT_CLUSTER=primary
$ python -m yapi examples/vault-init.yaml
2019-11-06 13:19:49,733 [INFO]: Starting yapi 0.1
2019-11-06 13:19:49,738 [INFO]: Loading examples/vault-init.yaml
2019-11-06 13:19:49,738 [INFO]: Start of stage: 01-Init Vault
2019-11-06 13:19:49,739 [INFO]: Body of request:
{
    "keys": [
        "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
    ],
    "secret_shares": "1",
    "secret_threshold": "1"
}
2019-11-06 13:19:49,936 [INFO]: Received status code OK 200 == 200
2019-11-06 13:19:49,936 [INFO]: Writing to examples/data/primary/init.json
2019-11-06 13:19:49,937 [INFO]: End of stage: 01-Init Vault
2019-11-06 13:19:49,937 [INFO]: Start of stage: 02-Unseal Vault
2019-11-06 13:19:49,937 [INFO]: Reading examples/data/primary/init.json , sub_vars: True
2019-11-06 13:19:49,938 [INFO]: Body of request:
{
    "keys": "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
}
2019-11-06 13:19:50,132 [INFO]: Received status code OK 200 == 200
2019-11-06 13:19:50,132 [INFO]: Writing to examples/data/primary/unsealed_response.json
2019-11-06 13:19:50,133 [INFO]: End of stage: 02-Unseal Vault
2019-11-06 13:19:50,133 [INFO]: Finished examples/vault-init.yaml
```

# Example file vault-init.yaml
```yaml
---
stages:
  - name: 01-Init Vault
    request:
      url: "{env_vars.VAULT_ADDR}"
      method: PUT
      json:
        secret_shares: 1
        secret_threshold: 1
        keys:
           - 7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2
    response:
      status_code: 200
      save:
        $ext:
          function: extensions.save_response
          extra_kwargs:
            path: "examples/data/{env_vars.VAULT_CLUSTER}/init.json"
  - name: 02-Unseal Vault
    request:
      url: "{env_vars.VAULT_ADDR}"
      method: PUT
      json:
        keys: "{ext.json_keys_0}"
        $ext:
          function: extensions.read_json
          extra_kwargs:
            path: "examples/data/{env_vars.VAULT_CLUSTER}/init.json"
            sub_vars: True
    response:
      status_code: 200
      save:
        $ext:
          function: extensions.save_response
          extra_kwargs:
            path: "examples/data/{env_vars.VAULT_CLUSTER}/unsealed_response.json"
```

### The first stage called `01-Init Vault`
- `env_vars.VAULT_ADDR` will be replaced by the enviromental variable `$VAULT_ADDR` as is the same with all variables starting with `env_vars.`
- Do a `GET` call to `url`
- The json sent to the API will be:
```json
{
    "keys": [
        "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
    ],
    "secret_shares": "1",
    "secret_threshold": "1"
}
```
- It expects a HTTP response of `200` or it will error out.
- It will save the output of the response as a json file under `data/{env_vars.VAULT_CLUSTER}/init.json`

### The second stage called `02-Unseal Vault` 
- Replace replace variables that start with `{env_vars.}` with environmental variables.
- Read `data/{env_vars.VAULT_CLUSTER}/init.json` and replace variables that start with `ext.` in the body with data from the json when `sub_vars` is set to `True`.
```json
  "json": {
    "keys": [
      "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
    ], 
```

Becomes:

```yaml
keys: "{ext.json_keys_0}"
```

- Do a `PUT` call to `url`
- With the json:
```json
{
    "keys": "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
}
```
- It will expect a `200` response code or error out.
- It will save the response to `data/{env_vars.VAULT_CLUSTER}/unsealed_response.json`


## TODO 
- [ ] Inject response as a variable to the next stage without having to read it
- [ ] Create `PyPi` package for easy installation