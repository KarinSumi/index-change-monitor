import requests
import json
import os
from datetime import datetime

def send_discord(message):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if webhook_url:
        requests.post(webhook_url, json={"content": message})

# ฟังก์ชันส่ง LINE Notify
def send_line_notify(message):
    line_token = os.environ.get('LINE_NOTIFY_TOKEN')
    if not line_token:
        print("ไม่พบ LINE_NOTIFY_TOKEN")
        return
    
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_token}'}
    data = {'message': message}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            print("ส่ง LINE Notify สำเร็จ")
        else:
            print(f"ส่ง LINE Notify ไม่สำเร็จ: {response.status_code}")
    except Exception as e:
        print(f"Error sending LINE: {e}")

# ฟังก์ชันดึงข้อมูล S&P 500 จาก Wikipedia (ตัวอย่าง)
def fetch_sp500_list():
    """
    ดึงรายชื่อหุ้นใน S&P 500 จาก Wikipedia
    (ในการใช้งานจริงอาจใช้ API อื่นที่เชื่อถือได้มากกว่า)
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, timeout=10)
        
        # ใช้ pandas อ่านตาราง HTML
        import pandas as pd
        tables = pd.read_html(response.text)
        df = tables[0]  # ตารางแรกคือรายชื่อหุ้น
        
        symbols = df['Symbol'].tolist()
        return set(symbols)
    except Exception as e:
        print(f"Error fetching S&P 500: {e}")
        return set()

# ฟังก์ชันดึงข้อมูล Nasdaq-100
def fetch_nasdaq100_list():
    """
    ดึงรายชื่อหุ้นใน Nasdaq-100 จาก Wikipedia
    """
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        response = requests.get(url, timeout=10)
        
        import pandas as pd
        tables = pd.read_html(response.text)
        df = tables[4]  # ตารางที่ 4 คือรายชื่อหุ้น (อาจเปลี่ยนได้)
        
        symbols = df['Ticker'].tolist()
        return set(symbols)
    except Exception as e:
        print(f"Error fetching Nasdaq-100: {e}")
        return set()

# ฟังก์ชันโหลดข้อมูลเก่า
def load_previous_data():
    try:
        with open('previous_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'sp500': [], 'nasdaq100': []}

# ฟังก์ชันบันทึกข้อมูลใหม่
def save_current_data(data):
    with open('previous_data.json', 'w') as f:
        json.dump(data, f, indent=2)

# ฟังก์ชันเปรียบเทียบและแจ้งเตือน
def compare_and_notify(index_name, previous_set, current_set):
    added = current_set - previous_set
    removed = previous_set - current_set
    
    if added or removed:
        message = f"\n🔔 {index_name} มีการเปลี่ยนแปลง!\n"
        message += f"วันที่: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if added:
            message += f"\n✅ เพิ่มเข้า {index_name}:\n"
            for symbol in sorted(added):
                message += f"  • {symbol}\n"
        
        if removed:
            message += f"\n❌ ถอดออกจาก {index_name}:\n"
            for symbol in sorted(removed):
                message += f"  • {symbol}\n"
        
        print(message)
        send_line_notify(message)
        return True
    else:
        print(f"✓ {index_name}: ไม่มีการเปลี่ยนแปลง")
        return False

def main():
    print(f"=== เริ่มตรวจสอบ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # ดึงข้อมูลปัจจุบัน
    current_sp500 = fetch_sp500_list()
    current_nasdaq100 = fetch_nasdaq100_list()
    
    print(f"S&P 500: {len(current_sp500)} หุ้น")
    print(f"Nasdaq-100: {len(current_nasdaq100)} หุ้น")
    
    # โหลดข้อมูลเก่า
    previous_data = load_previous_data()
    previous_sp500 = set(previous_data.get('sp500', []))
    previous_nasdaq100 = set(previous_data.get('nasdaq100', []))
    
    # ถ้าเป็นครั้งแรก (ไม่มีข้อมูลเก่า)
    if not previous_sp500 and not previous_nasdaq100:
        print("ครั้งแรก: บันทึกข้อมูลเริ่มต้น")
        save_current_data({
            'sp500': list(current_sp500),
            'nasdaq100': list(current_nasdaq100)
        })
        send_line_notify(f"🚀 เริ่มต้นติดตาม Index Changes\nS&P 500: {len(current_sp500)} หุ้น\nNasdaq-100: {len(current_nasdaq100)} หุ้น")
        return
    
    # เปรียบเทียบ
    sp500_changed = compare_and_notify("S&P 500", previous_sp500, current_sp500)
    nasdaq_changed = compare_and_notify("Nasdaq-100", previous_nasdaq100, current_nasdaq100)
    
    # บันทึกข้อมูลใหม่
    if sp500_changed or nasdaq_changed:
        save_current_data({
            'sp500': list(current_sp500),
            'nasdaq100': list(current_nasdaq100)
        })
        print("✓ บันทึกข้อมูลใหม่แล้ว")
    
    print("=== เสร็จสิ้น ===")

if __name__ == "__main__":
    main()
