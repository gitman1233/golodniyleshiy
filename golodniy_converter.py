from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

KAITEN_WEBHOOK_URL = 'https://golodniyleshiy.kaiten.ru/hooks/v1/49353cdaadef262aafa9df08cc0bb1935cd038cb4d028ec7933ab43462dbe523a62663a1d769a4c1bf38110d3f43bb562a4e02c24b08ac66397701674204cd2b'
KAITEN_TOKEN = 'a3d53c43-f6bd-4c97-87bb-8fdafbc36afc'  

def create_checklist(card_id, products):
    # Создаем чек-лист
    checklist_title = "Товары заказа"
    headers = {
        "Authorization": f"Bearer {KAITEN_TOKEN}",
        "Content-Type": "application/json"
    }
    checklist_payload = {
        "card_id": card_id,
        "title": checklist_title
    }
    resp = requests.post(
        "https://api.kaiten.ru/v1/checklists",
        json=checklist_payload,
        headers=headers
    )
    resp.raise_for_status()
    checklist_id = resp.json()["id"]


    for p in products:
        item_payload = {
            "checklist_id": checklist_id,
            "content": f"{p.get('name', '')}, Кол-во: {p.get('quantity', '')}, Цена: {p.get('price', '')}"
        }
        resp_item = requests.post(
            "https://api.kaiten.ru/v1/checklist_items",
            json=item_payload,
            headers=headers
        )
        resp_item.raise_for_status()

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

    # Cоздаем карточку через webhook
    resp = requests.post(KAITEN_WEBHOOK_URL, json=payload)
    print("Получен заказ с Tilda, вот JSON для Kaiten:\n", payload)
    print("Ответ Kaiten:", resp.status_code, resp.text)

    # Достаём ID карточки из ответа Kaiten и создаём чек-лист
    try:
        card_id = resp.json()['id']
        create_checklist(card_id, products)
        print("Чек-лист успешно добавлен!")
    except Exception as e:
        print("Ошибка добавления чек-листа:", e)

    return jsonify({"status": "ok", "kaiten_response": resp.status_code}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
