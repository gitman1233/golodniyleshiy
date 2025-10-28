from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

KAITEN_WEBHOOK_URL = 'https://golodniyleshiy.kaiten.ru/hooks/v1/49353cdaadef262aafa9df08cc0bb1935cd038cb4d028ec7933ab43462dbe523a62663a1d769a4c1bf38110d3f43bb562a4e02c24b08ac66397701674204cd2b'
KAITEN_API_URL_TMPL = 'https://golodniyleshiy.kaiten.ru/api/latest/cards/{card_id}/checklists'
KAITEN_TOKEN = 'a3d53c43-f6bd-4c97-87bb-8fdafbc36afc'

def create_checklist_and_items(card_id, products):
    url = KAITEN_API_URL_TMPL.format(card_id=card_id)
    headers = {
        "Authorization": f"Bearer {KAITEN_TOKEN}",
        "Content-Type": "application/json"
    }
    checklist_payload = {
        "name": "Чек-лист заказов голодный леший"
    }
    # 1. Создаём чек-лист
    resp = requests.post(url, json=checklist_payload, headers=headers)
    resp.raise_for_status()
    checklist_id = resp.json().get('id')
    print("API ответ по чек-листу:", resp.json())

    # 2. Добавляем товары как пункты чек-листа
    for idx, p in enumerate(products, 1):
        item_url = f"https://golodniyleshiy.kaiten.ru/api/latest/checklists/{checklist_id}/items"
        item_payload = {
            "content": f"{p.get('name', '')}, Кол-во: {p.get('quantity', '')}, Цена: {p.get('price', '')}",
            "sort_order": idx
        }
        resp_item = requests.post(item_url, json=item_payload, headers=headers)
        resp_item.raise_for_status()
        print(f"Добавлен пункт {idx}: {resp_item.json()}")

@app.route('/', methods=['POST'])
def webhook():
    data = request.json

    payment = data.get('payment', {})
    orderid = payment.get('orderid', '')
    title = f"Заказ #{orderid} с сайта Голодный Леший.ру"

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
    )

    payload = {
        "title": title,
        "description": description,
        "members": [],
        "links": [
            {
                "url": "https://golodniyleshiy.ru",
                "description": "Заказ через тильду с сайта golodniyleshiy.ru"
            }
        ]
    }

    resp = requests.post(KAITEN_WEBHOOK_URL, json=payload)
    print("Получен заказ с Tilda, вот JSON для Kaiten:\n", payload)
    print("Ответ Kaiten:", resp.status_code, resp.text)

    if resp.status_code == 200:
        try:
            card_id = resp.json().get('id')
            if card_id:
                create_checklist_and_items(card_id, products)
        except Exception as e:
            print("Ошибка при создании чек-листа и добавлении товаров:", e)

    return jsonify({"status": "ok", "kaiten_response": resp.status_code}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
