from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

KAITEN_WEBHOOK_URL = 'https://ВАШ_WEBHOOK_KAITEN'

@app.route('/', methods=['POST'])
def webhook():
    data = request.json

    payment = data.get('payment', {})
    orderid = payment.get('orderid', '')
    # Название карточки с номером заказа
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

    return jsonify({"status": "ok", "kaiten_response": resp.status_code}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
