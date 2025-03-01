## API examples

Примеры взаимодействия с API ГУК Краснодар

### Accounts

`GET https://lk.gukkrasnodar.ru/api/v1/user/accounts`

[accounts.json](tests/fixtures/accounts.json)

### Account Details

`POST https://lk.gukkrasnodar.ru/api/v1/user/account/info/extend`

```json
{
  "id_company": 1,
  "id_account": 12345
}
```

[account_detail.json](tests/fixtures/account_detail.json)

### Meter

`POST https://lk.gukkrasnodar.ru/api/v1/user/account/meters`

```json
{
  "id_company": 1,
  "id_account": 12345
}
```

[meters.json](tests/fixtures/meters.json)

### Meter history

`POST https://lk.gukkrasnodar.ru/api/v1/user/account/meter/measure/history`

```json
{
  "id_account": 12345,
  "id_company": 1,
  "offset": 0,
  "limit": null,
  "id_meters": [
    "67890"
  ],
  "begin_date": "2024-08-18T22:10:47.693Z",
  "end_date": "2025-02-18T22:10:47.692Z",
  "platform_type": "desktop",
  "sort_by": null,
  "descending": true
}
```

[meter_history.json](tests/fixtures/meter_history.json)
