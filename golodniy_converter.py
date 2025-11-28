from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime, timezone, timedelta


kaiten_time = datetime.now(timezone(timedelta(hours=3)))
date_now = kaiten_time.strftime("%d.%m.%Y")

app = Flask(__name__)

KAITEN_WEBHOOK_URL = 'https://golodniyleshiy.kaiten.ru/hooks/v1/49353cdaadef262aafa9df08cc0bb1935cd038cb4d028ec7933ab43462dbe523a62663a1d769a4c1bf38110d3f43bb562a4e02c24b08ac66397701674204cd2b'
KAITEN_API_URL_TMPL = 'https://golodniyleshiy.kaiten.ru/api/latest/cards/{card_id}/checklists'
KAITEN_TOKEN = 'a3d53c43-f6bd-4c97-87bb-8fdafbc36afc'

def format_product_line(p):
    # Используем простую формулу для наглядного результата
    qty = str(p.get('quantity', '')) if p.get('quantity', '') else ''
    # Соберём все опции в одну строку, например: "1 кг zero waste"
    options_str = ', '.join(
        filter(None, [op.get('variant', '') for op in p.get('options', [])])
    )
    parts = [
        p.get('name', ''),
        f"{qty}шт" if qty else '',
        options_str
    ]
    # убираем пустые элементы
    return ', '.join([part for part in parts if part])

def create_checklist_and_items(card_id, orderid, products):
    url = KAITEN_API_URL_TMPL.format(card_id=card_id)
    headers = {
        "Authorization": f"Bearer {KAITEN_TOKEN}",
        "Content-Type": "application/json"
    }
    checklist_payload = {
        "name": f"Заказ №{orderid}"
    }
    # 1. Создаём чек-лист
    resp = requests.post(url, json=checklist_payload, headers=headers)
    resp.raise_for_status()
    checklist_id = resp.json().get('id')
    print("API ответ по чек-листу:", resp.json())

    # 2. Добавляем товары как пункты чек-листа
    for idx, p in enumerate(products, 1):
        item_payload = {
            "text": format_product_line(p),
            "sort_order": idx
        }
        item_url = f"https://golodniyleshiy.kaiten.ru/api/latest/checklists/{checklist_id}/items"
        resp_item = requests.post(item_url, json=item_payload, headers=headers)
        resp_item.raise_for_status()
        print(f"Добавлен пункт {idx}: {resp_item.json()}")

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    print(data)

    payment = data.get('payment', {})
    orderid = payment.get('orderid', '')
    title = f"Заказ #{orderid}, {date_now}"

    products = payment.get('products', [])
    products_list = ""
    for idx, p in enumerate(products, 1):
        products_list += f"Товар {idx}: {p.get('name', '')}, Количество: {p.get('quantity', '')}, Цена: {p.get('price', '')}\n"
        options = p.get('options', [])
        for op in options:
            products_list += f"    Опция: {op.get('option', '')} — {op.get('variant', '')}\n"

    fio = data.get('ma_name') or payment.get('delivery_fio', '')

    description = (
        f"Номер заказа: {orderid}\n"
        f"Список товаров:\n{products_list}"
        f"Стоимость доставки: {payment.get('delivery_price', '')}\n"
        f"Промокод: {payment.get('promocode', '')}\n"
        f"Скидка: {payment.get('discountvalue', '')} ({payment.get('discount', '')})\n"
        f"Сумма без доставки: {payment.get('subtotal', '')}\n"
        f"Итого к оплате: {payment.get('amount', '')}\n"
        f"Способ доставки: {payment.get('delivery', '')}\n"
        f"Город доставки: {payment.get('delivery_city', '')}\n"
        f"Адрес пункта выдачи заказа: {payment.get('delivery_address', '')}\n"
        f"Телефон: {data.get('Phone', '') or data.get('ma_phone', '')}\n"
        f"Email: {data.get('Email', '') or data.get('ma_email', '')}\n"
        f"ФИО: {fio}\n"
        f"Комментарий к заказу: {data.get('comment', '')}\n"
    )

    payload = {
        "title": title,
        "description": description,
        "members": [],
        "links": []
    }

    resp = requests.post(KAITEN_WEBHOOK_URL, json=payload)
    print("Получен заказ с Tilda, вот JSON для Kaiten:\n", payload)
    print("Ответ Kaiten:", resp.status_code, resp.text)

    if resp.status_code == 200:
        try:
            card_id = resp.json().get('id')
            if card_id:
                create_checklist_and_items(card_id, orderid, products)
        except Exception as e:
            print("Ошибка при создании чек-листа и добавлении товаров:", e)

    return jsonify({"status": "ok", "kaiten_response": resp.status_code}), 200


@app.route('/ping', methods=['GET'])
def ping():
    return 'OK', 200  # Мгновенный ответ


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
