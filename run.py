import hashlib
import hmac
import base64
import requests
import time
from urllib.parse import quote_plus

from flask import Flask, render_template, request, redirect

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'APIKIPHU'
app.config['SESSION_PERMANENT'] = False

# Credenciales DEMOBANK
RECEIVER_ID = '497809'
SECRET = 'f69481bc962619b788649a8dacf7ccaed11e2f30'

# URL actual de instancia ngrok
#NGROK_URL = 'https://ddb5-181-42-131-238.ngrok-free.app'
NGROK_URL = 'https://example.com'  # URL genérica para prueba

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/cobrar')
def cobrar():
    return render_template('cobrar.html')

@app.route('/procesar_cobro', methods=['POST'])
def procesar_cobro():
    amount = request.form.get('amount')
    subject = request.form.get('description', '').strip()
    current_time = str(int(time.time()))

    # 1. Prepara datos como los espera Khipu
    data = {
        'receiver_id': RECEIVER_ID,
        'subject': subject,
        'body': 'Cobro generado desde prueba con Flask.',
        'amount': amount,
        'currency': 'CLP',
        'transaction_id': f'demo-{current_time}',
        'return_url': f'{NGROK_URL}/',
        'cancel_url': f'{NGROK_URL}/',
        'custom': 'ejemplo',
        'notify_url': f'{NGROK_URL}/notificar',
        'test': 'true'
    }

    # 2. Generación de la firma (versión corregida)
    # - Ordenar alfabéticamente
    # - Unir con & sin encoding
    # - No usa quote_plus en la firma
    sorted_params = '&'.join(f"{k}={v}" for k, v in sorted(data.items()))
    
    string_to_sign = f"POST\n/api/2.0/payments\n{sorted_params}"
    print("🔏 string_to_sign CORREGIDO:", string_to_sign)

    # 3. Firma HMAC-SHA256 (asegurameinto de encoding UTF-8)
    signature = hmac.new(
        SECRET.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature).decode('utf-8')
    print("🖋️ signature CORREGIDA:", signature)

    # 4. Headers (versión exacta que espera Khipu)
    headers = {
        'Authorization': f'Simple {RECEIVER_ID}:{signature}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    # 5. Enviar datos codi. (usar requests.post correctamente)
    try:
        response = requests.post(
            'https://khipu.com/api/2.0/payments',
            headers=headers,
            data=data,
            timeout=10
        )
        
        print("🔍 Raw Response:", response.text)
        
        if response.status_code == 200:
            return redirect(response.json()['payment_url'])
        else:
            return f"""
            <h3>Error {response.status_code}</h3>
            <pre>{response.text}</pre>
            <h4>Debug Info:</h4>
            <pre>string_to_sign: {string_to_sign}
            signature: {signature}
            </pre>
            """
            
    except Exception as e:
        return f"<h3>Error</h3><pre>{str(e)}</pre>"

@app.route('/notificar', methods=['POST'])
def notificar():
    contenido = request.form.to_dict()
    print("Notificacion recibida desde Khipu:", contenido)
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
