# Description of yapi

It allows to use declarative language (yaml) to talk to APIs and to save the response for future calls.

The main use case is to talk to [HashiCorp Vault API](https://www.vaultproject.io/api/overview.html).

It is heavily based on [Tavern-ci](https://github.com/taverntesting/tavern)
# Installing it
```
pip install yapi-ci
```
# How to use it
For this example we will use `http://httpbin.org/put` as `VAULT_ADDR`, this service will echo everything we send plus extra information about our request.
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
        mykeys:
           - 7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2
    response:
      status_code: 200
      save:
        $ext:
          function: extensions.save_response
          extra_kwargs:
            path: "examples/data/{env_vars.VAULT_CLUSTER}/init.json"
      body:
        headers: headers
        json_keys_list: json.mykeys
        json_secret_shares: json.secret_shares
        json_full: json
  - name: 02-Unseal Vault
    request:
      url: "{env_vars.VAULT_ADDR}"
      method: PUT
      json:
        mykeys: "ext.json.mykeys.to_list()"
        myheaders: "resp.headers.to_dict()"
        json_keys_list: "resp.json_keys_list.to_list()[0]"
        json_secret_shares: "test string {resp.json_secret_shares}"
        json_full: "resp.json_full.to_dict()"
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
    "mykeys": [
        "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
    ],
    "secret_shares": 1,
    "secret_threshold": 1
}
```
- It expects a HTTP response of `200` or it will error out.
- It will save the output of the response as a json file under `data/{env_vars.VAULT_CLUSTER}/init.json`
- It will try to convert the response to json and save them in variables for the next stage:
```yaml
    response:
    ...
      body:
        headers: headers
        json_keys_list: json.mykeys
        json_secret_shares: json.secret_shares
        json_full: json
```
### The second stage called `02-Unseal Vault` 
- Replace replace variables that start with `{env_vars.}` with environmental variables.
- Insert the variables saved in previous stages from `resp.` converting them to a python dictionary or list depending if we want a json object or array.
- Variables that have `{}` are used to `format` the string instead of replacing it with its value.
- 
```yaml
      json:
        mykeys: "ext.json.mykeys.to_list()"
        myheaders: "resp.headers.to_dict()"
        json_keys_list: "resp.json_keys_list.to_list()[0]"
        json_secret_shares: "test string {resp.json_secret_shares}"
        json_full: "resp.json_full.to_dict()"
```
- Read `data/{env_vars.VAULT_CLUSTER}/init.json` and replace variables that start with `ext.` in the body with data from the json when `sub_vars` is set to `True`.
```json
  "json": {
    "mykeys": [
      "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
    ],
```

Becomes:

```yaml
    mykeys: "ext.json.mykeys.to_list()"
```

- Do a `PUT` call to `url`
- With the json:
```json
{
    "json_full": {
        "mykeys": [
            "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
        ],
        "secret_shares": 1,
        "secret_threshold": 1
    },
    "json_keys_list": "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2",
    "json_secret_shares": "test string 1",
    "myheaders": {
        "Accept-Encoding": "identity",
        "Content-Length": "123",
        "Content-Type": "application/json",
        "Host": "httpbin.org"
    },
    "mykeys": [
        "7f921414b13ad05eb844dc349423765d857e8175b48c5854ada0e24e96924ac2"
    ]
}
```
- It will expect a `200` response code or error out.
- It will save the response to `data/{env_vars.VAULT_CLUSTER}/unsealed_response.json`


## TODO 
- [ ] Add Automated testing
- [ ] Add version tagging
- [ ] Add package automatic building from tags
