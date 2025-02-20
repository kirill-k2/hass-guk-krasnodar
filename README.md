# ЛК ГУК Краснодар для Home Assistant

Предоставление информации о текущем состоянии ваших лицевых счетов в ЛК ГУК Краснодар.
Передача показаний по счётчикам.

GUK Krasnodar personal cabinet information and status retrieval, with meter indications submission capabilities.

[![hacs_badge](https://img.shields.io/badge/HACS-Default-green.svg)](https://github.com/custom-components/hacs) [![Лицензия](https://img.shields.io/badge/%D0%9B%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D1%8F-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Поддержка](https://img.shields.io/badge/%D0%9F%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B8%D0%B2%D0%B0%D0%B5%D1%82%D1%81%D1%8F%3F-%D0%B4%D0%B0-green.svg)](https://github.com/kirill-k2/hass-guk-krasnodar/graphs/commit-activity)

## Установка

1. Установите как custom_components
1. Настройте yaml
1. Перезапустите Home Assistant

### Пример конфигурации YAML

```yaml
guk_krasnodar:
  username: user@domain.ru
  password: super_password
```

### Описание конфигурационной схемы

```yaml
# Файл `configuration.yaml`
guk_krasnodar:

  # Имя пользователя (номер лицевого счёта)
  # Обязательный параметр
  username: "..."

  # Пароль
  # Обязательный параметр
  password: "..."

  # Конфигурация по умолчанию для лицевых счетов
  # Необязательный параметр
  #  # Данная конфигурация применяется, если отсутствует  # конкретизация, указанная в разделе `accounts`.
  default:

    # Добавлять ли объект(-ы): Информация о лицевом счёте
    # Значение по умолчанию: истина (true)
    accounts: true | false

    # Добавлять ли объект(-ы): Счётчик коммунальных услуг
    # Значение по умолчанию: истина (true)
    meters: true | false
```

## Сервис отправки показаний

Пример отправки показаний счетчика `sensor.pokazanya_schetchika_vody` каждого 18го числа в 12:00.

```yaml
alias: Отправка показаний ГУК Краснодар
description: -|
  Отправлять показания по воде в 12 часов каждый 18й день месяца
trigger:
  - platform: time
    at: "12:00:00"
condition:
  - condition: template
    value_template: |
      {{ now().day == 18 }}
action:
  - service: guk_krasnodar.push_indications
    target:
      entity_id: sensor.guk_krasnodar_1_12345_meter_67890
    data:
      indications: |
        {{ states('sensor.pokazanya_schetchika_vody') | round(0) | int }}
      notification: true
mode: single
```

## Исправение ошибки с сертификатом (SSL: CERTIFICATE_VERIFY_FAILED)

При возникновении ошибки

> ERROR (MainThread) [custom_components.guk_krasnodar.config_flow] Authentication error: LoginError('Ошибка авторизации ResponseError("Общая ошибка запроса: ClientConnectorCertificateErro
r(ConnectionKey(host=\'lk.gukkrasnodar.ru\', port=443, is_ssl=True, ssl=True, proxy=None, proxy_auth=None, proxy_headers_hash=None), SSLCertVerificationError(1, \'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: una
ble to get local issuer certificate (_ssl.c:1018)\'))")')

Необходимо добавить корневой сертификат, используемый сайтом [lk.gukkrasnodar.ru](https://lk.gukkrasnodar.ru). 

На начало 2025 года это [GlobalSign](https://support.globalsign.com/ca-certificates/intermediate-certificates/alphassl-intermediate-certificates), непосредственно сертификат: 
[GlobalSign GCC R6 AlphaSSL CA 2023](https://secure.globalsign.com/cacert/gsgccr6alphasslca2023.crt).

Для Ubuntu/Debian, для установки выполнить на сервере:

```shell
curl https://secure.globalsign.com/cacert/gsgccr6alphasslca2023.crt -o gsgccr6alphasslca2023.crt
openssl x509 -in gsgccr6alphasslca2023.crt -inform DER -out "GlobalSign GCC R6 AlphaSSL CA 2023.crt"
sudo mkdir /usr/local/share/ca-certificates/extra
sudo mv "GlobalSign GCC R6 AlphaSSL CA 2023.crt" "/usr/local/share/ca-certificates/extra/GlobalSign GCC R6 AlphaSSL CA 2023.crt"
sudo update-ca-certificates
```

## API examples

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


## Credits

- [alryaz/hass-tns-energo](https://github.com/alryaz/hass-tns-energo) - за примеры реализации взаимодействия и базовые
  функции HA
- ГУК Краснодар - за адекватный публичный API
