import streamlit as st
import time
import threading
import queue
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session state
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'config' not in st.session_state: st.session_state.config = {}
if 'logs_queue' not in st.session_state: st.session_state.logs_queue = queue.Queue()
if 'automation_running' not in st.session_state: st.session_state.automation_running = False
if 'conversation_id' not in st.session_state: st.session_state.conversation_id = None
if 'sent_count' not in st.session_state: st.session_state.sent_count = 0

# Selenium function for real FB messaging
def send_fb_messages(config):
    logs = []
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        logger.info("Initializing ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Login with cookies
        driver.get("https://www.facebook.com/")
        time.sleep(2)
        for cookie_str in config.get('cookies', '').split(';'):
            if '=' in cookie_str:
                name, value = cookie_str.strip().split('=', 1)
                driver.add_cookie({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
        driver.refresh()
        time.sleep(3)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Logged in with cookies (check if valid)")

        # Go to Messenger and send messages
        driver.get(f"https://www.messenger.com/t/{config.get('chat_id')}")
        time.sleep(5)
        
        messages = [m.strip() for m in config.get('messages', '').split('\n') if m.strip()]
        sent_count = 0
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
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Sent to inbox: {msg[:20]}...")
                sent_count += 1
                st.session_state.sent_count = sent_count
            except Exception as e:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Error sending '{msg[:20]}...': {str(e)}")
        
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Complete! Sent {sent_count} messages to FB inbox")
        driver.quit()
    except Exception as e:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Setup Error: {str(e)}")
        logger.error(f"Setup failed: {str(e)}")
    
    return logs

# Background thread for automation
def run_automation():
    try:
        st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Automation started...\n")
        full_logs = send_fb_messages(st.session_state.config)
        for log in full_logs:
            if not st.session_state.automation_running:
                break
            st.session_state.logs_queue.put(log + "\n")
            time.sleep(0.5)
    except Exception as e:
        st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}\n")
    finally:
        st.session_state.automation_running = False

# Title
st.title("🚀 AYAZ E2EE FACEBOOK CONVO")
st.markdown("**Created by AYAZ** | Real FB Messaging with Selenium (Requires Proper Hosting)")

# Login Page
if not st.session_state.logged_in:
    st.subheader("Welcome Back! 🔐")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    if st.button("Login", type="primary"):
        if username and password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Logged in as {username}!")
            st.rerun()
        else:
            st.error("Please enter username and password.")
    
    st.markdown("---")
    st.caption("Made with ❤️ by AYAZ © 2025 All Rights Reserved")
else:
    # Sidebar for navigation
    page = st.sidebar.selectbox("Navigation", ["Configuration", "Automation", "Logout"])
    
    if page == "Configuration":
        st.subheader("Your Configuration ⚙️")
        
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = f"57{int(time.time())}"
        
        chat_id = st.text_input("Chat/Conversation ID", value=st.session_state.conversation_id, help="FB Convo ID (e.g., 123456789)")
        st.session_state.conversation_id = chat_id
        
        handler = st.text_input("Handlername", value="AYAZ BETA:", help="Your bot handler")
        
        delay = st.number_input("Delay (seconds)", min_value=1, value=30, help="Time between messages")
        
        st.subheader("Facebook Cookies (Required)")
        cookies = st.text_area("Paste your FB cookies here", 
                               placeholder="e.g., c_user=123; xs=abc; ...", height=100, 
                               help="Get from browser: F12 > Application > Cookies")
        
        messages = st.text_area("Messages (one per line)", 
                                placeholder="Message 1\nMessage 2\n...", 
                                help="Messages to send to FB inbox", height=150)
        
        if st.button("💾 Save Configuration", type="primary"):
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
            for key, value in st.session_state.config.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value[:50]}..." if len(str(value)) > 50 else value)
    
    elif page == "Automation":
        st.subheader("Automation Control 🤖")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Messages Sent", st.session_state.sent_count)
        with col2:
            status = "🟢 Running" if st.session_state.automation_running else "🔴 Stopped"
            st.metric("Status", status)
        with col3:
            total_logs = st.session_state.logs_queue.qsize()
            st.metric("Total Logs", total_logs)
        
        if st.button("🚀 Start E2EE", type="primary", disabled=not st.session_state.config):
            if not st.session_state.automation_running:
                st.session_state.automation_running = True
                st.session_state.sent_count = 0
                thread = threading.Thread(target=run_automation)
                thread.start()
                st.success("Automation started! Check live logs below.")
                st.rerun()
            else:
                st.warning("Already running!")
        
        if st.button("⏹️ Stop", type="secondary", disabled=not st.session_state.automation_running):
            st.session_state.automation_running = False
            st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Stopping automation...\n")
            st.info("Stopping...")
            st.rerun()
        
        # Live Logs
        st.subheader("🟢 Live Logs")
        log_container = st.empty()
        
        while True:
            try:
                new_log = st.session_state.logs_queue.get_nowait()
            except:
                break
            
            if new_log:
                log_container.text(new_log)
                time.sleep(0.1)
        
        if st.session_state.logs_queue.qsize() > 0:
            with st.expander("View Full Logs"):
                logs = [st.session_state.logs_queue.get() for _ in range(st.session_state.logs_queue.qsize())]
                for log in logs:
                    st.text(log)
    
    elif page == "Logout":
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

st.markdown("---")
st.caption("**Warning:** Real FB automation requires Chromium/Chromedriver on server. Use ethically! Made with ❤️ by AYAZ © 2025 All Rights Reserved")
