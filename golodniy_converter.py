from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Получен JSON из вебхука Tilda:")
    print(data)
    return 'ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render задает порт через переменную окружения
    app.run(host='0.0.0.0', port=port, debug=True)
