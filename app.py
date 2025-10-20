import streamlit as st
import time
import threading
import queue
from datetime import datetime

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
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
if 'login_method' not in st.session_state: st.session_state.login_method = "password"

# --------- REAL FACEBOOK MESSAGING FUNCTION ---------
def send_fb_messages_real(config):
    """REAL Facebook 1vs1 messages with BOTH login methods"""
    logs = []
    messages = [m.strip() for m in config.get('messages', '').split('\n') if m.strip()]
    sent_count = 0

    if not SELENIUM_AVAILABLE:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Selenium not available")
        return logs

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting Facebook...")

        # LOGIN METHOD SELECTION
        login_success = False
        
        if st.session_state.login_method == "cookies" and config.get('cookies'):
            # METHOD 1: COOKIES LOGIN
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔐 Trying cookies login...")
            driver.get("https://www.facebook.com/")
            time.sleep(3)
            
            # Add cookies
            cookies_added = 0
            for cookie_str in config.get('cookies', '').split(';'):
                cookie_str = cookie_str.strip()
                if '=' in cookie_str:
                    try:
                        name, value = cookie_str.split('=', 1)
                        cookie_dict = {
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': '.facebook.com'
                        }
                        driver.add_cookie(cookie_dict)
                        cookies_added += 1
                    except:
                        continue
            
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🍪 {cookies_added} cookies added")
            
            # Refresh to apply cookies
            driver.refresh()
            time.sleep(5)
            
            # Check if login successful
            if "facebook.com" in driver.current_url and "login" not in driver.current_url:
                login_success = True
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Cookies login successful!")
            else:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Cookies login failed")
        
        # METHOD 2: EMAIL/PASSWORD LOGIN (Fallback or primary)
        if not login_success and config.get('fb_email') and config.get('fb_password'):
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔐 Trying email/password login...")
            
            driver.get("https://www.facebook.com/")
            time.sleep(3)
            
            # Enter email
            try:
                email_field = driver.find_element(By.ID, "email")
                email_field.send_keys(config.get('fb_email'))
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Email entered")
            except:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Email field not found")
            
            # Enter password
            try:
                password_field = driver.find_element(By.ID, "pass")
                password_field.send_keys(config.get('fb_password'))
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Password entered")
            except:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Password field not found")
            
            # Click login
            try:
                login_button = driver.find_element(By.NAME, "login")
                login_button.click()
                time.sleep(5)
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Login button clicked")
            except:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Login button not found")
            
            # Check login success
            if "login" not in driver.current_url:
                login_success = True
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Password login successful!")
            else:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Password login failed")
        
        if not login_success:
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 💥 All login methods failed")
            driver.quit()
            return logs

        # MESSAGE SENDING PART (SAME)
        profile_url = f"https://www.facebook.com/{config.get('chat_id')}"
        driver.get(profile_url)
        time.sleep(5)
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📍 Profile page loaded")

        # Find and click Message button
        message_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'Message')]")
        if not message_buttons:
            message_buttons = driver.find_elements(By.XPATH, "//div[contains(text(), 'Message')]")
        
        if message_buttons:
            message_buttons[0].click()
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 💬 Message button clicked")
            time.sleep(5)
        else:
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Message button not found")
            driver.quit()
            return logs

        # Send messages
        for msg in messages:
            if not st.session_state.automation_running:
                break
            
            time.sleep(config.get('delay', 10))
            
            try:
                message_boxes = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
                if not message_boxes:
                    message_boxes = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                
                if message_boxes:
                    message_box = message_boxes[0]
                    message_box.click()
                    time.sleep(1)
                    message_box.clear()
                    message_box.send_keys(msg)
                    time.sleep(2)
                    message_box.send_keys(Keys.ENTER)
                    time.sleep(3)
                    
                    sent_count += 1
                    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ REAL SENT: {msg[:30]}...")
                    st.session_state.sent_count = sent_count
                else:
                    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Message box not found")
                    
            except Exception as e:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)}")

        driver.quit()
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 Complete! {sent_count} REAL messages sent")
        
    except Exception as e:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 💥 Error: {str(e)}")
    
    return logs

# Background thread
def run_automation():
    st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting...\n")
    logs = send_fb_messages_real(st.session_state.config)
    for log in logs:
        st.session_state.logs_queue.put(log + "\n")
    st.session_state.automation_running = False

# ----------------- Streamlit UI -----------------
st.title("🚀 AYAZ REAL FACEBOOK MESSENGER")
st.markdown("**Dual Login Methods** | Created by AYAZ")

if not st.session_state.logged_in:
    st.subheader("🔐 Choose Login Method")
    
    login_method = st.radio("Select Login Type:", 
                           ["Email/Password", "Cookies"],
                           index=0)
    
    st.session_state.login_method = "password" if login_method == "Email/Password" else "cookies"
    
    if login_method == "Email/Password":
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("📧 Facebook Email", placeholder="your_email@example.com")
        with col2:
            password = st.text_input("🔑 Facebook Password", type="password", placeholder="Your password")
        
        if st.button("🔓 Login with Email/Password"):
            if email and password:
                st.session_state.logged_in = True
                st.session_state.config['fb_email'] = email
                st.session_state.config['fb_password'] = password
                st.success("✅ Email/Password saved securely!")
                st.rerun()
    
    else:  # Cookies method
        cookies = st.text_area("🍪 Facebook Cookies", 
                             height=100,
                             placeholder="cookie1=value1; cookie2=value2; ...",
                             help="Paste your Facebook cookies here")
        
        if st.button("🔓 Login with Cookies"):
            if cookies:
                st.session_state.logged_in = True
                st.session_state.config['cookies'] = cookies
                st.success("✅ Cookies saved!")
                st.rerun()

else:
    page = st.sidebar.selectbox("Navigation", ["Configuration", "Automation", "Logout"])
    
    if page == "Configuration":
        st.subheader("⚙️ Message Configuration")
        
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = "username"
            
        col1, col2 = st.columns(2)
        
        with col1:
            chat_id = st.text_input("👤 Facebook Username/ID", 
                                  value=st.session_state.conversation_id,
                                  placeholder="amit.sharma.12")
            delay = st.slider("⏱️ Delay (seconds)", min_value=5, max_value=60, value=10)
        
        with col2:
            messages = st.text_area("💌 Messages (one per line)", 
                                  height=200,
                                  placeholder="Hello! 👋\nKya haal hai?")
        
        if st.button("💾 Save Configuration"):
            st.session_state.config.update({
                'chat_id': chat_id,
                'delay': delay,
                'messages': messages
            })
            st.session_state.conversation_id = chat_id
            st.success("✅ Configuration saved!")
            
            # Show login method info
            if st.session_state.login_method == "password":
                st.info(f"🔐 Login: Email/Password | Target: {chat_id}")
            else:
                st.info(f"🔐 Login: Cookies | Target: {chat_id}")
    
    elif page == "Automation":
        st.subheader("🤖 Automation Control")
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Sent", st.session_state.sent_count)
        with col2: 
            status = "🟢 Running" if st.session_state.automation_running else "🔴 Stopped"
            st.metric("Status", status)
        with col3: 
            method = "Password" if st.session_state.login_method == "password" else "Cookies"
            st.metric("Login Method", method)
        
        if st.button("🚀 Start REAL Messaging", disabled=not st.session_state.config):
            if not st.session_state.automation_running:
                st.session_state.automation_running = True
                st.session_state.sent_count = 0
                threading.Thread(target=run_automation, daemon=True).start()
                st.success("🚀 Started! Refresh logs to see updates.")
        
        if st.button("⏹️ Stop", disabled=not st.session_state.automation_running):
            st.session_state.automation_running = False
            st.session_state.logs_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️ Stopped\n")
        
        # Logs
        st.subheader("📜 Live Logs")
        log_container = st.empty()
        logs_display = ""
        while not st.session_state.logs_queue.empty():
            logs_display += st.session_state.logs_queue.get_nowait()
        
        if logs_display:
            log_container.text_area("", logs_display, height=300)
        
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    elif page == "Logout":
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

st.markdown("---")
st.caption("Dual Login Facebook Messenger | ❤️ by AYAZ")
