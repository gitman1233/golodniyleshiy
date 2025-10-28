from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Укажи свой реальный Kaiten webhook URL!
KAITEN_WEBHOOK_URL = 'https://golodniyleshiy.kaiten.ru/hooks/v1/9a7e2854d97c60055c825e2f3ebd74f273b055e790890900f265874b1f34b2ba81555cf9125996574fa40be62123e0d0d47d0bdb7f06a24ae999540c841a7e47'

@app.route('/', methods=['POST'])
def webhook():
    data = request.json

    # Название карточки
    title = "Заказ с сайта Голодный Леший.ру"

    payment = data.get('payment', {})
    product = payment.get('products', [{}])[0]

    description = (
        f"Товар: {product.get('name', '')}\n"
        f"Количество: {product.get('quantity', '')}\n"
        f"Цена: {product.get('price', '')}\n"
        f"Стоимость доставки: {payment.get('delivery_price', '')}\n"
        f"Промокод: {payment.get('promocode', '')}\n"
        f"Скидка: {payment.get('discountvalue', '')} ({payment.get('discount', '')})\n"
        f"Сумма без доставки: {payment.get('subtotal', '')}\n"
        f"Итого к оплате: {payment.get('amount', '')}\n"
        f"Способ доставки: {payment.get('delivery', '')}\n"
        f"Город доставки: {payment.get('delivery_city', '')}\n"
        f"Адрес пункта выдачи заказа: {payment.get('delivery_address', '')}\n"
        f"Телефон: {data.get('Phone', '')}\n"
        f"Email: {data.get('Email', '')}\n"
        f"ФИО: {data.get('ma_name', '')}\n"
    )

    # Формируем итоговый JSON для Kaiten
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

    # Отправка в Kaiten
    resp = requests.post(KAITEN_WEBHOOK_URL, json=payload)

    # Лог вывода для дебага
    print("Получен заказ с Tilda, вот JSON для Kaiten:\n", payload)
    print("Ответ Kaiten:", resp.status_code, resp.text)

    return jsonify({"status": "ok", "kaiten_response": resp.status_code}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
