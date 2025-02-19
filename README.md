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

## API examples

### Accounts

`GET https://lk.gukkrasnodar.ru/api/v1/user/accounts`

```json
{
  "success": true,
  "accounts": [
    {
      "inn": "2311104687",
      "status": 2,
      "account": "230123456",
      "address": "ул.Красная, д.1 кв.1",
      "id_account": 12345,
      "id_company": 1,
      "status_text": "Подтверждено",
      "company_name": "ООО \"ГУК-Краснодар\"",
      "company_full_name": "Общество с ограниченной ответственностью \"Городская управляющая компания - Краснодар\"",
      "response_not_reading": 0
    }
  ]
}
```

### Account

`POST https://lk.gukkrasnodar.ru/api/v1/user/account/info/extend`

```json
{
  "id_company": 1,
  "id_account": 12345
}
```

```json
{
  "info": [
    {
      "name": "Лицевой счет",
      "value": "230123456",
      "field_order": "1"
    },
    {
      "name": "Адрес",
      "value": "ул.Красная, д.1 кв.1",
      "field_order": "2"
    },
    {
      "name": "Оплачиваемая площадь",
      "value": "99.99",
      "field_order": "3"
    },
    {
      "name": "Кол-во чел. на л/с",
      "field_order": "4"
    },
    {
      "name": "Задолженность (основные услуги)",
      "value": "1234.56",
      "field_order": "5"
    },
    {
      "name": "Начисление за Февраль 2025 (основные услуги)",
      "value": "6543.21",
      "field_order": "7"
    }
  ],
  "bills": [
    {
      "name": "Основные услуги",
      "index": "1",
      "value": "BillModule"
    }
  ],
  "periods": [
    {
      "year": "2025",
      "month": "1",
      "period": "24301",
      "month_name": "Январь",
      "period_name": "Январь 2025"
    },
    ...
    {
      "year": "2008",
      "month": "1",
      "period": "24097",
      "month_name": "Январь",
      "period_name": "Январь 2008"
    }
  ],
  "success": true,
  "message_after": {
    "icon": true,
    "type": "info",
    "title": null,
    "value": "* Для просмотра квитанции в формате PDF (Adobe Portable Document Format) Вам понадобится программа Adobe® Acrobat® Reader (Программа распространяется бесплатно) Если на Вашем компьютере эта программа не установлена, Вы можете <a href=\"https://get.adobe.com/ru/reader/\" target=\"blank\">загрузить ее с официального сайта Adobe Systems Inc.</a>"
  },
  "show_payonline": false
}
```

### Meter

`POST https://lk.gukkrasnodar.ru/api/v1/user/account/meters`

```json
{
  "id_company": 1,
  "id_account": 12345
}
```

```json
{
  "meter": [
    {
      "info": [
        "Состояние: В работе",
        "Дата следующей поверки: 01.01.2099",
        "Модель: Информация отсутствует Производитель: Не указан",
        "Показания переданы: Да. Расчетный объем: 12."
      ],
      "title": "1.ИПУ по ХВС (78901)",
      "detail": "Последнее показание 123 от 18.02.2025г.",
      "capacity": "5",
      "id_meter": "67890",
      "precision": "3"
    }
  ],
  "success": true,
  "volume_allow": false,
  "message_after": null,
  "accept_measure_set": {
    "accept": true,
    "message": null
  }
}
```

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

```json
{
  "success": true,
  "message_after": null,
  "meter_measure_history": {
    "header": [
      {
        "name": "Дата показаний",
        "index": "1",
        "value": "field_order",
        "property": "date",
        "sortable": "true"
      },
      {
        "name": "Счетчик",
        "index": "2",
        "value": "name",
        "property": null,
        "sortable": "true"
      },
      {
        "name": "Показание",
        "index": "3",
        "value": "value",
        "property": null,
        "sortable": "false"
      },
      {
        "name": "Объем",
        "index": "4",
        "value": "volume",
        "property": null,
        "sortable": "false"
      },
      {
        "name": "Период учета",
        "index": "5",
        "value": "period_name",
        "property": null,
        "sortable": "false"
      }
    ],
    "default": {
      "sort_by": "field_order",
      "descending": "true",
      "total_items": "5",
      "rows_per_page": "50"
    },
    "meter_name": [
      {
        "icon": null,
        "name": "ИПУ по ХВС (78901)",
        "id_meter": "67890",
        "field_order": "1"
      }
    ],
    "meter_measure": [
      {
        "date": "18.02.2025",
        "icon": null,
        "info": "Объем:10. Период учета: Февраль 2025",
        "name": "ИПУ по ХВС (78901)",
        "value": "123",
        "volume": "10",
        "id_meter": "67890",
        "field_order": "1",
        "period_name": "Февраль 2025"
      },
      {
        "date": "20.01.2025",
        "icon": null,
        "info": "Объем:10. Период учета: Январь 2025",
        "name": "ИПУ по ХВС (78901)",
        "value": "113",
        "volume": "10",
        "id_meter": "67890",
        "field_order": "3",
        "period_name": "Январь 2025"
      },
      {
        "date": "18.12.2024",
        "icon": null,
        "info": "Объем:3. Период учета: Декабрь 2024",
        "name": "ИПУ по ХВС (78901)",
        "value": "103",
        "volume": "3",
        "id_meter": "67890",
        "field_order": "4",
        "period_name": "Декабрь 2024"
      },
      {
        "date": "20.08.2024",
        "icon": null,
        "info": "Объем:1. Период учета: Август 2024",
        "name": "ИПУ по ХВС (78901)",
        "value": "100",
        "volume": "1",
        "id_meter": "67890",
        "field_order": "5",
        "period_name": "Август 2024"
      }
    ],
    "count_meter_measure": "5"
  }
}
```

## Credits

- [alryaz/hass-tns-energo](https://github.com/alryaz/hass-tns-energo) за примеры реализации взаимодействия и базовые
  функции HA
