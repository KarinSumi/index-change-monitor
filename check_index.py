import requests
import json
import os
import io
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
import pandas as pd # ย้ายมา import ข้างบนเพื่อความชัวร์

# ==================== CONFIGURATION ====================

# Header เพื่อหลอก Server ว่าเราเป็น Browser (แก้ปัญหา Wikipedia Block)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ==================== NOTIFICATION FUNCTIONS ====================

def send_discord(message, priority="normal"):
    """ส่งข้อความไป Discord Webhook"""
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        print("❌ ไม่พบ DISCORD_WEBHOOK")
        return False
    
    # เพิ่ม emoji ตาม priority
    if priority == "high":
        message = "🚨 **ALERT** " + message
    
    data = {
        "content": message,
        "username": "Index Monitor Bot v2.0",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2111/2111615.png"
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        if response.status_code == 204:
            print("✅ ส่ง Discord สำเร็จ")
            return True
        else:
            print(f"❌ ส่ง Discord ไม่สำเร็จ: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending Discord: {e}")
        return False


# ==================== S&P OFFICIAL SOURCES ====================

def check_sp_press_releases():
    """
    ตรวจจาก S&P Dow Jones Indices Official Press Releases
    ความน่าเชื่อถือ: ⭐⭐⭐⭐⭐ (Official Source)
    """
    print("\n📰 [S&P Official] ตรวจสอบ Press Releases...")
    
    try:
        # ใช้ PR Newswire RSS Feed สำหรับ S&P DJI
        url = "https://www.prnewswire.com/rss/news-releases/s-p-dow-jones-indices-list.rss"
        feed = feedparser.parse(url)
        
        recent_changes = []
        keywords = ['s&p 500', 'sp 500', 'will replace', 'will join', 'added to', 'removed from']
        
        # ตรวจ entries ล่าสุด (7 วันย้อนหลัง)
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for entry in feed.entries[:20]:
            title = entry.title.lower()
            
            # ตรวจหา keywords ที่เกี่ยวข้อง
            if any(keyword in title for keyword in keywords):
                # Parse วันที่
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date >= cutoff_date:
                        recent_changes.append({
                            'source': 'S&P Official',
                            'title': entry.title,
                            'link': entry.link,
                            'date': pub_date.strftime('%Y-%m-%d'),
                            'confidence': '⭐⭐⭐⭐⭐'
                        })
                except:
                    pass
        
        if recent_changes:
            print(f"  ✅ พบประกาศ {len(recent_changes)} รายการ")
        else:
            print("  ℹ️  ไม่พบประกาศใหม่")
        
        return recent_changes
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def scrape_sp_announcements():
    """
    Scrape จากหน้า S&P DJI Media Center
    ความน่าเชื่อถือ: ⭐⭐⭐⭐⭐ (Official Source)
    """
    print("\n📰 [S&P Media Center] ตรวจสอบประกาศ...")
    
    try:
        url = "https://www.spglobal.com/spdji/en/media-center/news-announcements/"
        # ใช้ Global HEADERS
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # หาข่าวที่เกี่ยวกับ index changes
        announcements = []
        keywords = ['announces changes', 'will replace', 's&p 500', 's&p midcap', 's&p smallcap']
        
        # ค้นหา links ที่มี keywords
        for link in soup.find_all('a', href=True):
            text = link.get_text().lower()
            if any(keyword in text for keyword in keywords):
                announcements.append({
                    'source': 'S&P Media Center',
                    'title': link.get_text().strip(),
                    'link': link['href'] if link['href'].startswith('http') else f"https://www.spglobal.com{link['href']}",
                    'confidence': '⭐⭐⭐⭐⭐'
                })
        
        if announcements:
            print(f"  ✅ พบประกาศ {len(announcements[:5])} รายการ")
            return announcements[:5]  # จำกัด 5 รายการ
        else:
            print("  ℹ️  ไม่พบประกาศใหม่")
            return []
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


# ==================== NASDAQ OFFICIAL SOURCES ====================

def check_nasdaq_press_releases():
    """
    ตรวจจาก Nasdaq Official Press Releases
    ความน่าเชื่อถือ: ⭐⭐⭐⭐⭐ (Official Source)
    """
    print("\n📰 [Nasdaq Official] ตรวจสอบ Press Releases...")
    
    try:
        # ใช้ Nasdaq Investor Relations RSS
        url = "https://ir.nasdaq.com/rss/news-releases/default.aspx"
        feed = feedparser.parse(url)
        
        recent_changes = []
        keywords = ['nasdaq-100', 'nasdaq 100', 'reconstitution', 'added to', 'removed from']
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for entry in feed.entries[:20]:
            title = entry.title.lower()
            
            if any(keyword in title for keyword in keywords):
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date >= cutoff_date:
                        recent_changes.append({
                            'source': 'Nasdaq Official',
                            'title': entry.title,
                            'link': entry.link,
                            'date': pub_date.strftime('%Y-%m-%d'),
                            'confidence': '⭐⭐⭐⭐⭐'
                        })
                except:
                    pass
        
        if recent_changes:
            print(f"  ✅ พบประกาศ {len(recent_changes)} รายการ")
        else:
            print("  ℹ️  ไม่พบประกาศใหม่")
        
        return recent_changes
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


# ==================== WIKIPEDIA (BACKUP) ====================

def fetch_sp500_list():
    """
    ดึงรายชื่อหุ้นใน S&P 500 จาก Wikipedia
    ความน่าเชื่อถือ: ⭐⭐⭐ (อาจล่าช้า 1-2 วัน)
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # ใส่ Headers เพื่อแก้ปัญหา 0 stocks
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # ใช้ io.StringIO เพื่อ parse HTML
        tables = pd.read_html(io.StringIO(response.text))
        df = tables[0]
        
        symbols = df['Symbol'].tolist()
        print(f"  ✅ Wikipedia S&P 500: {len(symbols)} หุ้น")
        return set(symbols)
    except Exception as e:
        print(f"  ❌ Wikipedia S&P 500 Error: {e}")
        return set()


def fetch_nasdaq100_list():
    """
    ดึงรายชื่อหุ้นใน Nasdaq-100 จาก Wikipedia
    ความน่าเชื่อถือ: ⭐⭐⭐ (อาจล่าช้า 1-2 วัน)
    """
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        # ใส่ Headers เพื่อแก้ปัญหา 0 stocks
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # ใช้ io.StringIO เพื่อ parse HTML
        tables = pd.read_html(io.StringIO(response.text))
        
        # หมายเหตุ: Nasdaq Index บน Wiki อาจขยับตำแหน่งได้ (ปกติ 4)
        target_table = None
        for table in tables:
            # หาตารางที่มี col ชื่อ Ticker หรือ Symbol
            if 'Ticker' in table.columns:
                target_table = table
                break
            elif 'Symbol' in table.columns:
                target_table = table
                break
        
        if target_table is not None:
            if 'Ticker' in target_table.columns:
                symbols = target_table['Ticker'].tolist()
            else:
                symbols = target_table['Symbol'].tolist()
            
            print(f"  ✅ Wikipedia Nasdaq-100: {len(symbols)} หุ้น")
            return set(symbols)
        else:
            print("  ⚠️ Wikipedia Nasdaq-100: ไม่พบตารางหุ้น")
            return set()
            
    except Exception as e:
        print(f"  ❌ Wikipedia Nasdaq-100 Error: {e}")
        return set()


# ==================== DATA STORAGE ====================

def load_previous_data():
    """โหลดข้อมูลเก่า"""
    try:
        with open('previous_data.json', 'r') as f:
            data = json.load(f)
            print("✅ โหลดข้อมูลเก่าสำเร็จ")
            return data
    except FileNotFoundError:
        print("⚠️  ไม่พบข้อมูลเก่า (ครั้งแรก)")
        return {
            'sp500': [],
            'nasdaq100': [],
            'last_check': None,
            'press_releases_checked': []
        }


def save_current_data(data):
    """บันทึกข้อมูลใหม่"""
    try:
        data['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('previous_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("✅ บันทึกข้อมูลสำเร็จ")
    except Exception as e:
        print(f"❌ Error saving: {e}")


# ==================== COMPARISON ====================

def compare_and_notify(index_name, previous_set, current_set):
    """เปรียบเทียบและแจ้งเตือน"""
    added = current_set - previous_set
    removed = previous_set - current_set
    
    if added or removed:
        message = f"\n🔔 **{index_name} มีการเปลี่ยนแปลง!**\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"🔍 แหล่งข้อมูล: Wikipedia (⭐⭐⭐)\n"
        
        if added:
            message += f"\n✅ **เพิ่มเข้า:**\n"
            for symbol in sorted(added):
                message += f"  • `{symbol}`\n"
        
        if removed:
            message += f"\n❌ **ถอดออก:**\n"
            for symbol in sorted(removed):
                message += f"  • `{symbol}`\n"
        
        message += f"\n📊 จำนวนปัจจุบัน: {len(current_set)} หุ้น"
        
        print(message)
        send_discord(message, priority="high")
        return True
    else:
        print(f"  ✅ {index_name}: ไม่มีการเปลี่ยนแปลง")
        return False


# ==================== MAIN ====================

def main():
    print("=" * 70)
    print("🤖 Index Monitor Bot v2.0 - Multi-Source Edition")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. ตรวจจาก Official Press Releases
    print("\n" + "="*70)
    print("📰 PHASE 1: ตรวจสอบ OFFICIAL PRESS RELEASES")
    print("="*70)
    
    all_announcements = []
    
    # S&P Official Sources
    sp_press = check_sp_press_releases()
    all_announcements.extend(sp_press)
    
    sp_media = scrape_sp_announcements()
    all_announcements.extend(sp_media)
    
    # Nasdaq Official Sources
    nasdaq_press = check_nasdaq_press_releases()
    all_announcements.extend(nasdaq_press)
    
    # แจ้งเตือนถ้าพบประกาศใหม่
    if all_announcements:
        message = "🚨 **พบประกาศใหม่จาก Official Sources!**\n\n"
        
        for item in all_announcements[:10]:  # จำกัด 10 รายการ
            message += f"**{item['source']}** {item.get('confidence', '')}\n"
            message += f"📌 {item['title']}\n"
            message += f"🔗 {item['link']}\n"
            if 'date' in item:
                message += f"📅 {item['date']}\n"
            message += "\n"
        
        if len(all_announcements) > 10:
            message += f"_และอีก {len(all_announcements) - 10} รายการ..._\n"
        
        send_discord(message, priority="high")
    
    # 2. ตรวจจาก Wikipedia (สำรอง)
    print("\n" + "="*70)
    print("📊 PHASE 2: ตรวจสอบ WIKIPEDIA (Backup)")
    print("="*70)
    
    current_sp500 = fetch_sp500_list()
    current_nasdaq100 = fetch_nasdaq100_list()
    
    # โหลดข้อมูลเก่า
    previous_data = load_previous_data()
    previous_sp500 = set(previous_data.get('sp500', []))
    previous_nasdaq100 = set(previous_data.get('nasdaq100', []))
    
    # ถ้าเป็นครั้งแรก หรือ ข้อมูลเก่าว่างเปล่า (กรณี error 0 ครั้งก่อน)
    if not previous_sp500 and not previous_nasdaq100:
        print("\n🚀 ครั้งแรก: บันทึกข้อมูลเริ่มต้น")
        save_current_data({
            'sp500': list(current_sp500),
            'nasdaq100': list(current_nasdaq100),
            'press_releases_checked': []
        })
        
        init_msg = (
            f"🚀 **เริ่มต้น Index Monitor Bot v2.0**\n\n"
            f"📊 **S&P 500**: {len(current_sp500)} หุ้น\n"
            f"📊 **Nasdaq-100**: {len(current_nasdaq100)} หุ้น\n\n"
            f"✅ Bot พร้อมทำงาน!\n"
            f"🔍 ตรวจสอบจาก:\n"
            f"  • S&P Official Press Releases ⭐⭐⭐⭐⭐\n"
            f"  • Nasdaq Official Press Releases ⭐⭐⭐⭐⭐\n"
            f"  • Wikipedia (สำรอง) ⭐⭐⭐"
        )
        send_discord(init_msg)
        return
    
    # เปรียบเทียบ
    print("\n🔍 เปรียบเทียบข้อมูล...")
    sp_changed = compare_and_notify("S&P 500", previous_sp500, current_sp500)
    nasdaq_changed = compare_and_notify("Nasdaq-100", previous_nasdaq100, current_nasdaq100)
    
    # บันทึก
    if sp_changed or nasdaq_changed or all_announcements:
        save_current_data({
            'sp500': list(current_sp500),
            'nasdaq100': list(current_nasdaq100),
            'press_releases_checked': [item['link'] for item in all_announcements]
        })
    
    # สรุป
    print("\n" + "="*70)
    print("✅ เสร็จสิ้นการตรวจสอบ")
    print("="*70)
    
    if not all_announcements and not sp_changed and not nasdaq_changed:
        print("\n✨ ไม่มีการเปลี่ยนแปลงในรอบนี้")


if __name__ == "__main__":
    main()
