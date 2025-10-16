import streamlit as st
import time
import threading
import queue
from datetime import datetime

# Optional: selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.keys import Keys
    SELENIUM_AVAILABLE = True
except:
    SELENIUM_AVAILABLE = False

# Session state
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'config' not in st.session_state: st.session_state.config = {}
if 'logs_queue' not in st.session_state: st.session_state.logs_queue = queue.Queue()
if 'automation_running' not in st.session_state: st.session_state.automation_running = False
if 'conversation_id' not in st.session_state: st.session_state.conversation_id = None
if 'sent_count' not in st.session_state: st.session_state.sent_count = 0

# --------- Automation function ---------
def send_fb_messages(config, simulate=True):
    """Send FB messages via Selenium (or simulate if Chrome unavailable)"""
    logs = []
    messages = [m.strip() for m in config.get('messages', '').split('\n') if m.strip()]
    sent_count = 0

    if simulate or not SELENIUM_AVAILABLE:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Simulation mode ON. Messages will not actually be sent.")
        for msg in messages:
            if not st.session_state.automation_running:
                break
            time.sleep(config.get('delay', 2))  # simulate delay
            sent_count += 1
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Simulated send: {msg[:30]}...")
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Simulation complete. {sent_count} messages 'sent'.")
        return logs

    # Selenium actual sending
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ChromeDriver initialized.")

        driver.get("https://www.facebook.com/")
        time.sleep(2)
        for cookie_str in config.get('cookies', '').split(';'):
            if '=' in cookie_str:
                name, value = cookie_str.strip().split('=', 1)
                driver.add_cookie({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
        driver.refresh()
        time.sleep(3)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Logged in with cookies (check if valid)")

        driver.get(f"https://www.messenger.com/t/{config.get('chat_id')}")
        time.sleep(5)

        for msg in messages:
            if not st.session_state.automation_running:
                break
            time.sleep(config.get('delay', 30))
            try:
                message_box = driver.find_element("xpath", "//div[@role='textbox'][@contenteditable='true']")
                message_box.clear()
                message_box.send_keys(msg)
                time.sleep(1)
                message_box.send_keys(Keys.ENTER)
                time.sleep(2)
                sent_count += 1
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Sent: {msg[:30]}...")
                st.session_state.sent_count = sent_count
            except Exception as e:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Error sending '{msg[:30]}...': {str(e)}")
        driver.quit()
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Complete! Sent {sent_count} messages")
    except Exception as e:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Selenium setup error: {str(e)}")
    
    return logs

# Background thread
def run_automation(simulate=True):
    st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Automation started...\n")
    logs = send_fb_messages(st.session_state.config, simulate=simulate)
    for log in logs:
        st.session_state.logs_queue.put(log + "\n")
    st.session_state.automation_running = False

# ----------------- Streamlit UI -----------------
st.title("🚀 AYAZ E2EE FACEBOOK CONVO (Modified)")
st.markdown("**Created by AYAZ** | Simulated FB Messaging in Streamlit")

# Login
if not st.session_state.logged_in:
    st.subheader("Welcome! 🔐")
    username = st.text_input("Username", placeholder="Enter username")
    password = st.text_input("Password", type="password", placeholder="Enter password")
    
    if st.button("Login"):
        if username and password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Logged in as {username}")
            st.rerun()
        else:
            st.error("Enter username and password")
else:
    page = st.sidebar.selectbox("Navigation", ["Configuration", "Automation", "Logout"])
    
    if page == "Configuration":
        st.subheader("Configuration ⚙️")
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = f"57{int(time.time())}"
        
        chat_id = st.text_input("Chat ID", value=st.session_state.conversation_id)
        st.session_state.conversation_id = chat_id
        handler = st.text_input("Handler", value="AYAZ BETA:")
        delay = st.number_input("Delay (seconds)", min_value=1, value=2)
        cookies = st.text_area("FB Cookies", height=100)
        messages = st.text_area("Messages (one per line)", height=150)
        
        if st.button("💾 Save Config"):
            st.session_state.config = {
                'chat_id': chat_id,
                'handler': handler,
                'delay': delay,
                'cookies': cookies,
                'messages': messages
            }
            st.success("Configuration saved!")
            st.rerun()
        
        if st.session_state.config:
            st.markdown("**Saved Config:**")
            for k,v in st.session_state.config.items():
                st.write(f"{k}: {str(v)[:50]}{'...' if len(str(v))>50 else ''}")
    
    elif page == "Automation":
        st.subheader("Automation Control 🤖")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Messages Sent", st.session_state.sent_count)
        with col2: st.metric("Status", "🟢 Running" if st.session_state.automation_running else "🔴 Stopped")
        with col3: st.metric("Total Logs", st.session_state.logs_queue.qsize())
        
        if st.button("🚀 Start Automation", disabled=not st.session_state.config):
            if not st.session_state.automation_running:
                st.session_state.automation_running = True
                st.session_state.sent_count = 0
                simulate = not SELENIUM_AVAILABLE  # Cloud fallback
                threading.Thread(target=run_automation, args=(simulate,), daemon=True).start()
                st.success("Automation started! Click 'Refresh Logs' below to see updates.")
            else:
                st.warning("Already running!")
        
        if st.button("⏹️ Stop", disabled=not st.session_state.automation_running):
            st.session_state.automation_running = False
            st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Stopping automation...\n")
            st.info("Stopping automation...")
        
        # Logs display
        st.subheader("🟢 Live Logs")
        log_container = st.empty()
        logs_display = ""
        while not st.session_state.logs_queue.empty():
            logs_display += st.session_state.logs_queue.get_nowait()
        if logs_display:
            log_container.text(logs_display)
        
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    elif page == "Logout":
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

st.markdown("---")
st.caption("Simulated FB automation for Streamlit. Made with ❤️ by AYAZ © 2025")
