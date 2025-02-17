# ЛК ГУК Краснодар для Home Assistant

> Предоставление информации о текущем состоянии ваших лицевых счетов в ЛК ГУК Краснодар.
> Передача показаний по счётчикам.
>
> GUK Krasnodar personal cabinet information and status retrieval, with meter indications submission capabilities.

## Установка

1. Установите как custom_components
1. Настройте yaml
1. Перезапустите Home Assistant

### Пример конфигурации YAML
```yaml
guk_krasnodar:
  username: 1234567890
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

## Credits

- [alryaz/hass-tns-energo](https://github.com/alryaz/hass-tns-energo) за примеры реализации взаимодействия и базовые функции HA
