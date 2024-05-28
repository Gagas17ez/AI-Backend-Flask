from flask import Flask, request, jsonify
import joblib
import requests
import time

app = Flask(__name__)

# Muat model yang telah disimpan
model_cpu_path = 'models/cpu_new_model.joblib'
model_cpu = joblib.load(model_cpu_path)

model_vga_path = 'models/vga_new_model.joblib'
model_vga = joblib.load(model_vga_path)

model_am4_path = 'models/am4_new_model.joblib'
model_am4 = joblib.load(model_am4_path)

model_lga1200_path = 'models/lga1200_new_model.joblib'
model_lga1200 = joblib.load(model_lga1200_path)

model_lga1700_path = 'models/lga1700_new_model.joblib'
model_lga1700 = joblib.load(model_lga1700_path)

model_psu_path = 'models/psu_new_model.joblib'
model_psu = joblib.load(model_psu_path)

model_ssd_path = 'models/ssd_new_model.joblib'
model_ssd = joblib.load(model_ssd_path)

model_ddr4_path = 'models/ddr4_new_model.joblib'
model_ddr4 = joblib.load(model_ddr4_path)


@app.route('/predict/pc', methods=['POST'])
def predict_pc():
    try:
        # Pastikan bahwa request mengandung JSON
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()

        # Lakukan prediksi menggunakan model yang telah dimuat
        cpu_id = get_cpu_recommendation(input_data)  
        socket_cpu, nama_cpu, watt_cpu = get_cpu_details(cpu_id)
        watt_cpu_int = int(watt_cpu)

        if socket_cpu == "AM4":
            mobo_id = get_am4_recommendation(input_data)
        elif socket_cpu == "LGA 1200":
            mobo_id = get_lga1200_recommendation(input_data)
        elif socket_cpu == "LGA 1700":
            mobo_id = get_lga1700_recommendation(input_data)

        nama_mobo, socket_mobo, socket_ram, socket_nvme = get_mobo_details(mobo_id)

        vga_id = get_vga_recommendation(input_data)
        nama_vga, watt_vga = get_vga_details(vga_id)
        watt_vga_int = int(watt_vga)
        
        psu_id = get_psu_recommendation(input_data)
        nama_psu, watt_psu = get_psu_details(psu_id)
        watt_psu_int = int(watt_psu)

        ssd_id = get_ssd_recommendation(input_data)
        nama_ssd, tipe_ssd = get_ssd_details(ssd_id)

        ddr4_id = get_ddr4_recommendation(input_data)
        nama_ram, tipe_ram = get_ram_details(ddr4_id)

        watt_default_mobo = 40
        watt_default_ram = 10
        watt_default_ssd = 10
        total_wattage = watt_cpu_int + watt_vga_int + watt_default_mobo + watt_default_ssd + watt_default_ram

        compatibility_passed = validate_compatibility(socket_cpu, socket_mobo, total_wattage, watt_psu_int, socket_ram, tipe_ram, tipe_ssd, socket_nvme)
        
        if compatibility_passed:
            return jsonify({
                'status': 'success',
                'data': {
                    'CPU': cpu_id,
                    'VGA': vga_id,
                    'Motherboard': psu_id,
                    'DDR4': ssd_id,
                    'SSD': ddr4_id,
                    'PSU': psu_id,
                }
            }), 200
        
        return jsonify({
                'status': 'error',
                'cpu': socket_cpu,
                'mobo': socket_mobo,
                'watt': total_wattage,
                'psu': watt_psu,
                'socket ram': socket_ram,
                'tipe ram': tipe_ram,
                'tipe ssd': tipe_ssd,
                'ssd': nama_ssd,
        }), 400
            
        
    except Exception as e:
        # Tangani kesalahan yang mungkin terjadi
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
def validate_compatibility(socket_cpu, socket_mobo, total_wattage, watt_psu, socket_ram, tipe_ram, tipe_ssd, socket_nvme):
    # Check CPU and motherboard compatibility
    if socket_cpu != socket_mobo:
        return False

    # Check if the total wattage is within the PSU capacity
    if total_wattage > watt_psu:
        return False

    # Check RAM compatibility
    socket_ram_cleaned = ''.join(socket_ram.split()).lower()
    tipe_ram_cleaned = tipe_ram.lower()
    if tipe_ram_cleaned not in socket_ram_cleaned:
        return False

    if tipe_ssd.lower() == "nvme":
        if "no" in socket_nvme.lower():
             return False

    return True

def get_vga_details(vga_id):
    # Menentukan header dengan User-Agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    try:
        response = requests.get(f'https://ta.infak.in/api/v2/vga/{vga_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["message"] == "success":
                nama_vga = data["data"][0]["NamaVGA"]
                watt_vga = data["data"][0]["PowerConsumption"]
                return nama_vga, watt_vga
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def get_cpu_recommendation(input_data):
    # Siapkan data untuk prediksi
    # Misalnya, kita asumsikan model membutuhkan semua fitur dalam bentuk array 2D
    # Ini hanya contoh, sesuaikan dengan kebutuhan model Anda
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['upgrade']]
    prediction = model_cpu.predict([features])
    return str(prediction[0])

def get_cpu_details(cpu_id):
    # Menentukan header dengan User-Agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    try:
        response = requests.get(f'https://ta.infak.in/api/v2/cpu/{cpu_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["message"] == "success":
                socket_cpu = data["data"][0]["Socket"]
                nama_cpu = data["data"][0]["NamaCPU"]
                watt_cpu = data["data"][0]["DefaultTDP"]
                return socket_cpu, nama_cpu, watt_cpu
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
 

def get_mobo_details(mobo_id):
    # Menentukan header dengan User-Agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    try:
        response = requests.get(f'https://ta.infak.in/api/v2/motherboard/{mobo_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["message"] == "success":
                nama_mobo = data["data"][0]["NamaMobo"]
                socket_mobo = data["data"][0]["SocketMobo"]
                socket_ram = data["data"][0]["MemoryType"]
                socket_nvme = data["data"][0]["M2Slot"]
                return nama_mobo, socket_mobo, socket_ram, socket_nvme
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def get_ssd_details(ssd_id):
    # Menentukan header dengan User-Agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    try:
        response = requests.get(f'https://ta.infak.in/api/v2/storage/{ssd_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["message"] == "success":
                nama_ssd = data["data"][0]["NamaStorage"]
                tipe_ssd = data["data"][0]["TypeStorage"]
                return nama_ssd, tipe_ssd
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def get_ram_details(vga_id):
    # Menentukan header dengan User-Agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    try:
        response = requests.get(f'https://ta.infak.in/api/v2/ram/{vga_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["message"] == "success":
                nama_ram = data["data"][0]["NamaRam"]
                tipe_ram = data["data"][0]["MemoryType"]
                return nama_ram, tipe_ram
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def get_psu_details(psu_id):
    # Menentukan header dengan User-Agent
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    try:
        response = requests.get(f'https://ta.infak.in/api/v2/psu/{psu_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["message"] == "success":
                nama_psu = data["data"][0]["NamaPSU"]
                watt_psu = data["data"][0]["WattPSU"]
                return nama_psu, watt_psu
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

@app.route('/predict/cpu', methods=['POST'])
def predict_cpu():
    try:
        # Pastikan bahwa request mengandung JSON
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()

        # Lakukan prediksi menggunakan model yang telah dimuat
        response = get_cpu_recommendation(input_data)

        # Kembalikan respons dengan status code 200 (OK)
        return jsonify({
            'status': 'success',
            'data': response
        }), 200
    except Exception as e:
        # Tangani kesalahan yang mungkin terjadi
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
def get_vga_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['warna']]
    prediction = model_vga.predict([features])
    return str(prediction[0])

@app.route('/predict/vga', methods=['POST'])
def predict_vga():
    try:
        # Pastikan bahwa request mengandung JSON
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()

        # Lakukan prediksi menggunakan model yang telah dimuat
        response = get_vga_recommendation(input_data)

        # Kembalikan respons dengan status code 200 (OK)
        return jsonify({
            'status': 'success',
            'data': response
        }), 200
    except Exception as e:
        # Tangani kesalahan yang mungkin terjadi
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def get_am4_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['warna'], input_data['upgrade']]
    prediction = model_am4.predict([features])
    return str(prediction[0])

@app.route('/predict/am4', methods=['POST'])
def predict_am4():
    try:
        # Pastikan bahwa request mengandung JSON
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()

        # Lakukan prediksi menggunakan model yang telah dimuat
        response = get_vga_recommendation(input_data)

        # Kembalikan respons dengan status code 200 (OK)
        return jsonify({
            'status': 'success',
            'data': response
        }), 200
    except Exception as e:
        # Tangani kesalahan yang mungkin terjadi
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
def get_lga1200_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['warna'], input_data['upgrade']]
    prediction = model_lga1200.predict([features])
    return str(prediction[0])

@app.route('/predict/lga1200', methods=['POST'])
def predict_lga1200():
    try:
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()
        response = get_lga1200_recommendation(input_data)
        return jsonify({'status': 'success', 'data': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_lga1700_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], 
                input_data['ram'], input_data['warna']]
    prediction = model_lga1700.predict([features])
    return str(prediction[0])

@app.route('/predict/lga1700', methods=['POST'])
def predict_lga1700():
    try:
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()
        response = get_lga1700_recommendation(input_data)
        return jsonify({'status': 'success', 'data': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_psu_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['warna'], input_data['upgrade']]
    prediction = model_psu.predict([features])
    return str(prediction[0])

@app.route('/predict/psu', methods=['POST'])
def predict_psu():
    try:
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()
        response = get_psu_recommendation(input_data)
        return jsonify({'status': 'success', 'data': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_ssd_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['upgrade']]
    prediction = model_ssd.predict([features])
    return str(prediction[0])

@app.route('/predict/ssd', methods=['POST'])
def predict_ssd():
    try:
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()
        response = get_ssd_recommendation(input_data)
        return jsonify({'status': 'success', 'data': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def get_ddr4_recommendation(input_data):
    features = [input_data['budget'], input_data['kebutuhan'], input_data['storage'],
                input_data['ram'], input_data['warna']]
    prediction = model_ddr4.predict([features])
    return str(prediction[0])

@app.route('/predict/ddr4', methods=['POST'])
def predict_ddr4():
    try:
        if not request.is_json:
            return jsonify({'error': 'Missing JSON in request'}), 400

        input_data = request.get_json()
        response = get_ddr4_recommendation(input_data)
        return jsonify({'status': 'success', 'data': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
       


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
