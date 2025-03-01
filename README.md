[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Лицензия](https://img.shields.io/badge/%D0%9B%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D1%8F-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# ЛК ГУК Краснодар для Home Assistant

Предоставление информации о текущем состоянии ваших лицевых счетов в ЛК ГУК Краснодар.
Передача показаний по счётчикам воды.

GUK Krasnodar personal cabinet information and status retrieval, with meter indications submission capabilities.

## Установка

### Способ 1: Через HACS

1. Установите HACS ([инструкция по установке на оф. сайте](https://hacs.xyz/docs/installation/installation/))
2. [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kirill-k2&repository=hass-guk-krasnodar&category=integration)
3. Установите последнюю версию компонента, нажав на кнопку `Установить` (`Install`)
4. Перезапустите Home Assistant

### Способ 2: Вручную

1. Скачайте архив [актуальной версии](https://github.com/kirill-k2/hass-guk-krasnodar/releases/latest)
2. Распакуйте и Вручную скопируйте папку `guk_krasnodar` в директорию `/config/custom_components`
3. Перезапустите Home Assistant

## Настройка компонента:

### Способ 1: Через настройки

1. Перейдите в [Настройки](https://my.home-assistant.io/redirect/config)
2. Пункт `Устройства и службы`, в нем [Интеграции](https://my.home-assistant.io/redirect/integrations)
3. Пункт [Добавить интеграцию](https://my.home-assistant.io/redirect/config_flow_start?domain=guk_krasnodar)
4. Далее - `Поиск`, указать **GUK Krasnodar**

ИЛИ нажмите

[![Добавить интеграцию](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=guk_krasnodar)

Далее, следуя инструкциям, укажите логин/пароль и, при необходимости, выберите лицевой счет.

### Способ 2: Через YAML

Пример конфигурации YAML:

```yaml
guk_krasnodar:
  username: user@domain.ru
  password: super_password
```

#### Описание конфигурационной схемы

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

## Использование

### Обновление

По-умолчанию обновление баланса и последних переданных показаний производиться раз в 6 часов и чаще обновлять не
рекомендуется.

### Служба передачи показаний - `tns_energo.push_indications`

Служба передачи показаний позволяет отправлять показания по счётчикам в личный кабинет, и
имеет следующий набор параметров:

| Название                   | Описание                                                                                               |
|----------------------------|--------------------------------------------------------------------------------------------------------|
| `target`                   | Выборка целевых объектов, для которых требуется передавать показания                                   |
| `data`.`indications`       | Значение показаний без десятичной части (до точки)                                                     |
| `data`.`indication_entity` | Объект, из которого будет взято значение для отправки. Применяется если в значении показаний указан 0. |

#### Пример автоматизации

Пример отправки показаний счетчика `sensor.pokazanya_schetchika_vody` каждого 18го числа в 12:00.

```yaml
automation:
  - alias: Отправка показаний ГУК Краснодар
    description: -|
      Отправлять показания по воде в 12 часов каждый 18-й день месяца
    trigger:
      - platform: time
        at: "12:00"
    condition:
      - condition: template
        value_template: { { now().day == 18 } }
    action:
      - service: guk_krasnodar.push_indications
        target:
          entity_id: sensor.guk_krasnodar_1_12345_meter_67890
        data:
          indications: 0
          indication_entity: sensor.pokazanya_schetchika_vody
    mode: single
```

## Исправление ошибки с сертификатом

При возникновении ошибки `SSL: CERTIFICATE_VERIFY_FAILED`:

> ERROR (MainThread) [custom_components.guk_krasnodar.config_flow] Authentication error: LoginError('Ошибка авторизации
> ResponseError("Общая ошибка запроса: ClientConnectorCertificateError(ConnectionKey(host=\'lk.gukkrasnodar.ru\',
> port=443, is_ssl=True, ssl=True, proxy=None, proxy_auth=None,
> proxy_headers_hash=None), SSLCertVerificationError(1, \'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
> unable to get local issuer certificate (_ssl.c:1018)\'))")')

Необходимо в систему добавить корневой сертификат используемый сайтом [lk.gukkrasnodar.ru](https://lk.gukkrasnodar.ru).

На начало 2025 года
это [GlobalSign](https://support.globalsign.com/ca-certificates/intermediate-certificates/alphassl-intermediate-certificates),
непосредственно сертификат доступен по
ссылке: [GlobalSign GCC R6 AlphaSSL CA 2023](https://secure.globalsign.com/cacert/gsgccr6alphasslca2023.crt).

### Ubuntu/Debian

Для установки корневого сертификата выполнить на сервере:

```shell
curl https://secure.globalsign.com/cacert/gsgccr6alphasslca2023.crt -o gsgccr6alphasslca2023.crt
openssl x509 -in gsgccr6alphasslca2023.crt -inform DER -out "GlobalSign GCC R6 AlphaSSL CA 2023.crt"
sudo mkdir /usr/local/share/ca-certificates/extra
sudo mv "GlobalSign GCC R6 AlphaSSL CA 2023.crt" "/usr/local/share/ca-certificates/extra/GlobalSign GCC R6 AlphaSSL CA 2023.crt"
sudo update-ca-certificates
```

### Docker Compose

1. Сохранить `sgccr6alphasslca2023.crt` в папке `./homeassistant/certs`
2. Исправить `docker-compose.yml` по образу и подобию:
    ```yml
      homeassistant:
        volumes:
          - ./homeassistant/certs:/usr/local/share/ca-certificates/extra:ro
        entrypoint:
          [ "sh", "-c", "([ ! -f /etc/ssl/certs/.updated ] && cat /usr/local/share/ca-certificates/extra/*.crt >> /etc/ssl/certs/ca-certificates.crt && touch /etc/ssl/certs/.updated ); /init" ]
        ...
    ```
3. Перезапустите контейнер
    ```shell
    docker-compose up -d    
    ```

## Credits

- [alryaz/hass-tns-energo](https://github.com/alryaz/hass-tns-energo) - за примеры реализации взаимодействия и базовые
  функции HA
- ГУК Краснодар - за адекватный публичный API
