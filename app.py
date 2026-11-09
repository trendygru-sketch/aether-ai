import streamlit as st
import sqlite3
import requests
from datetime import date, datetime, timedelta
from duckduckgo_search import DDGS
from PIL import Image
import io
import os

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# ==============================================================================
# AETHER AI — PROFESSIONAL ENTERPRISE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Aether AI - Cosmic Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject PWA Meta Tags & Manifest for Mobile Installation
st.markdown("""
    <head>
        <link rel="manifest" href="data:application/json;charset=utf-8,%7B%22name%22%3A%22Aether%20AI%22%2C%22short_name%22%3A%22Aether%22%2C%22start_url%22%3A%22%2F%22%2C%22display%22%3A%22standalone%22%2C%22background_color%22%3A%22%2313131A%22%2C%22theme_color%22%3A%22%23d946ef%22%2C%22icons%22%3A%5B%7B%22src%22%3A%22https%3A%2F%2Fapi.iconify.design%2Flucide%3Asparkles.svg%3Fcolor%3D%2523d946ef%22%2C%22sizes%22%3A%22192x192%22%2C%22type%22%3A%22image%2Fsvg%2Bxml%22%7D%5D%7D">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Aether AI">
    </head>
""", unsafe_allow_html=True)

# ==============================================================================
# DATABASE INITIALIZATION & SUBSCRIPTIONS / LIMITS
# ==============================================================================
@st.cache_resource
def init_aether_db():
    db_path = 'aether_production.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS threads (
                    thread_id TEXT PRIMARY KEY, 
                    title TEXT, 
                    created_at TIMESTAMP, 
                    project_name TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    thread_id TEXT, 
                    role TEXT, 
                    content TEXT, 
                    timestamp TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    project_name TEXT PRIMARY KEY, 
                    instructions TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS library (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    filename TEXT, 
                    file_type TEXT, 
                    content TEXT,
                    upload_date TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, 
                    password TEXT, 
                    tier TEXT,
                    tokens INTEGER,
                    image_count INTEGER,
                    last_image_date TEXT
                )''')
    conn.commit()
    return conn

conn = init_aether_db()
cursor = conn.cursor()

# Session State Setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "tier" not in st.session_state:
    st.session_state.tier = "Free"
if "tokens" not in st.session_state:
    st.session_state.tokens = 0
if "theme" not in st.session_state:
    st.session_state.theme = "Light"
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = "thread_default_1"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "editing_thread_id" not in st.session_state:
    st.session_state.editing_thread_id = None
if "menu_thread_id" not in st.session_state:
    st.session_state.menu_thread_id = None
if "nav_choice" not in st.session_state:
    st.session_state.nav_choice = "💬 Chat Studio"

# ==============================================================================
# AUTHENTICATION GATE
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown("""
        <div style='max-width: 420px; margin: 60px auto; padding: 2.5rem; background: #1E1E2A; border: 1px solid #2D2D3B; border-radius: 20px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
            <div style='font-size: 3rem; margin-bottom: 10px; background: linear-gradient(135deg, #d946ef, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>✦</div>
            <h2 style='color: #F3F4F6; margin-bottom: 5px;'>Aether AI Portal</h2>
            <p style='color: #9CA3AF; font-size: 0.9rem; margin-bottom: 25px;'>Sign in to your cosmic workspace.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_auth1, col_auth2 = st.columns([1, 1])
    with st.container():
        auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
        
        with auth_tab1:
            login_user = st.text_input("Username", key="login_u")
            login_pass = st.text_input("Password", type="password", key="login_p")
            if st.button("Log In", use_container_width=True):
                cursor.execute("SELECT password, tier, tokens FROM users WHERE username=?", (login_user,))
                user_record = cursor.fetchone()
                if user_record and user_record[0] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.tier = user_record[1]
                    st.session_state.tokens = user_record[2]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
        with auth_tab2:
            new_user = st.text_input("Choose Username", key="reg_u")
            new_pass = st.text_input("Choose Password", type="password", key="reg_p")
            sub_key = st.text_input("VIP Access Code (Optional for 300 Tokens / Pro)", type="password")
            if st.button("Register Account", use_container_width=True):
                if new_user and new_pass:
                    assigned_tier = "Pro (1 Month)" if sub_key == "AETHER2026VIP" else "Free"
                    assigned_tokens = 300 if sub_key == "AETHER2026VIP" else 0
                    try:
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", 
                                       (new_user, new_pass, assigned_tier, assigned_tokens, 0, str(date.today())))
                        conn.commit()
                        st.session_state.logged_in = True
                        st.session_state.username = new_user
                        st.session_state.tier = assigned_tier
                        st.session_state.tokens = assigned_tokens
                        st.success(f"Account created successfully! Tier: {assigned_tier}")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists. Choose another.")
                else:
                    st.warning("Please fill in both username and password.")
    st.stop()

# Theme Token Definitions
if st.session_state.theme == "Light":
    bg_main = "#FFFFFF"
    bg_sidebar = "#F9FBFD"
    bg_surface = "#FFFFFF"
    text_primary = "#111118"
    text_secondary = "#6B7280"
    border_color = "#E5E7EB"
    user_bubble_bg = "linear-gradient(135deg, #7c3aed 0%, #2563eb 100%)"
    user_bubble_text = "#FFFFFF"
    ai_text_color = "#111118"
    hover_bg = "#F3F4F6"
    code_bg = "#F3F4F6"
    shadow_depth = "0 10px 30px -8px rgba(124, 58, 237, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.8)"
else:
    bg_main = "#13131A"
    bg_sidebar = "#181822"
    bg_surface = "#1E1E2A"
    text_primary = "#F3F4F6"
    text_secondary = "#9CA3AF"
    border_color = "#2D2D3B"
    user_bubble_bg = "linear-gradient(135deg, #8b5cf6 100%, #3b82f6 0%)"
    user_bubble_text = "#FFFFFF"
    ai_text_color = "#F3F4F6"
    hover_bg = "#252533"
    code_bg = "#13131A"
    shadow_depth = "0 12px 35px -8px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)"

# Inject Custom CSS with Neon Plasma Vapor Gas Animation
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes plasmaVaporDrift {{
        0% {{
            border-color: #d946ef;
            background: radial-gradient(circle at 20% 50%, rgba(217, 70, 239, 0.18) 0%, rgba(147, 51, 234, 0.12) 50%, rgba(168, 85, 247, 0.06) 100%);
            box-shadow: 0 0 30px rgba(217, 70, 239, 0.4), 0 0 60px rgba(147, 51, 234, 0.25), inset 0 0 25px rgba(217, 70, 239, 0.2);
        }}
        33% {{
            border-color: #c084fc;
            background: radial-gradient(circle at 80% 20%, rgba(192, 132, 252, 0.22) 0%, rgba(217, 70, 239, 0.12) 50%, rgba(124, 58, 237, 0.08) 100%);
            box-shadow: 0 0 40px rgba(192, 132, 252, 0.5), 0 0 70px rgba(217, 70, 239, 0.3), inset 0 0 35px rgba(192, 132, 252, 0.25);
        }}
        66% {{
            border-color: #a855f7;
            background: radial-gradient(circle at 50% 80%, rgba(168, 85, 247, 0.2) 0%, rgba(192, 132, 252, 0.15) 50%, rgba(147, 51, 234, 0.06) 100%);
            box-shadow: 0 0 35px rgba(168, 85, 247, 0.45), 0 0 65px rgba(192, 132, 252, 0.25), inset 0 0 30px rgba(168, 85, 247, 0.22);
        }}
        100% {{
            border-color: #d946ef;
            background: radial-gradient(circle at 20% 50%, rgba(217, 70, 239, 0.18) 0%, rgba(147, 51, 234, 0.12) 50%, rgba(168, 85, 247, 0.06) 100%);
            box-shadow: 0 0 30px rgba(217, 70, 239, 0.4), 0 0 60px rgba(147, 51, 234, 0.25), inset 0 0 25px rgba(217, 70, 239, 0.2);
        }}
    }}

    .stApp {{
        background-color: {bg_main} !important;
        color: {text_primary} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        animation: fadeIn 0.35s ease forwards;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {bg_sidebar} !important;
        border-right: 1px solid {border_color} !important;
    }}

    section[data-testid="stSidebar"] .stButton > button {{
        background-color: transparent !important;
        color: {text_primary} !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.45rem 0.6rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-weight: 500 !important;
        font-size: 0.93rem !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background-color: {hover_bg} !important;
        color: #d946ef !important;
    }}

    .user-message-container {{
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1.5rem;
        width: 100%;
    }}
    .user-bubble {{
        background: {user_bubble_bg};
        color: {user_bubble_text};
        padding: 0.9rem 1.25rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        box-shadow: {shadow_depth};
        font-size: 1rem;
        font-weight: 500;
        line-height: 1.6;
    }}

    .ai-message-container {{
        display: flex;
        justify-content: flex-start;
        margin-bottom: 1.75rem;
        width: 100%;
        gap: 14px;
    }}
    .ai-avatar {{
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #d946ef, #06b6d4);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        flex-shrink: 0;
    }}
    .ai-response-body {{
        color: {ai_text_color};
        font-size: 1.02rem;
        line-height: 1.75;
        max-width: 84%;
        background: {bg_surface};
        padding: 1.2rem 1.4rem;
        border-radius: 14px;
        border: 1px solid {border_color};
    }}

    .stChatInput textarea {{
        color: {text_primary} !important;
        border: 3px solid #d946ef !important;
        border-radius: 22px !important;
        padding: 0.9rem 1.3rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.02rem !important;
        animation: plasmaVaporDrift 5s infinite ease-in-out !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Ensure default thread exists
cursor.execute("SELECT COUNT(*) FROM threads WHERE thread_id=?", (st.session_state.current_thread_id,))
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO threads VALUES (?, ?, ?, ?)", (st.session_state.current_thread_id, "New Chat", datetime.now(), "General"))
    conn.commit()

if not st.session_state.messages:
    cursor.execute("SELECT role, content FROM messages WHERE thread_id=? ORDER BY id ASC", (st.session_state.current_thread_id,))
    st.session_state.messages = [{"role": r, "content": c} for r, c in cursor.fetchall()]

SYSTEM_PROMPT = """You are Aether AI, an advanced cosmic intelligence ecosystem created by Siddhartha Saud. Keep answers precise and conversational."""

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: space-between; padding: 6px 0 14px 0;'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <div style='background: linear-gradient(135deg, #d946ef, #06b6d4); width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;'>✦</div>
                <h2 style='font-size: 1.15rem; font-weight: 700; margin: 0;'>Aether AI</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("✨ New chat", use_container_width=True):
        new_id = f"thread_{int(datetime.now().timestamp())}"
        st.session_state.current_thread_id = new_id
        cursor.execute("INSERT INTO threads VALUES (?, ?, ?, ?)", (new_id, "New Chat", datetime.now(), "General"))
        conn.commit()
        st.session_state.messages = []
        st.rerun()

    st.markdown(f"<p style='color: {text_secondary}; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-top: 15px;'>Navigation</p>", unsafe_allow_html=True)
    
    nav_options = [
        ("💬 Chat Studio", "Chat Studio"),
        ("🎨 Image Studio", "Image Studio"),
        ("🛠️ Explore AI Tools", "Explore AI Tools"),
        ("📚 Resource Library", "Resource Library"),
        ("📂 Projects", "Projects"),
        ("💳 Subscription & Billing", "Billing"),
        ("⚙️ Settings", "Settings")
    ]

    for label, key_name in nav_options:
        if st.button(label, key=f"nav_{key_name}", use_container_width=True):
            st.session_state.nav_choice = label
            st.rerun()

    nav_selection = st.session_state.nav_choice

    st.markdown(f"<hr style='border-color: {border_color}; margin: 15px 0;'>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='padding: 4px 0;'>
            <div style='font-weight: 600; color: {text_primary};'>👤 {st.session_state.username}</div>
            <div style='font-size: 0.75rem; color: #d946ef; font-weight: 700;'>Tier: {st.session_state.tier}</div>
            <div style='font-size: 0.75rem; color: #06b6d4; font-weight: 700;'>Tokens Available: {st.session_state.tokens}</div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    user_api_key = st.text_input("Groq API Key", value="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", type="password")

# ==============================================================================
# ROUTING
# ==============================================================================
if nav_selection == "💬 Chat Studio":
    st.caption(f"Active Chat Limit: Maximum **100 messages** per thread.")
    
    # Check message limit (100 msgs per chat)
    if len(st.session_state.messages) >= 100:
        st.warning("⚠️ You have reached the maximum limit of 100 messages for this chat thread. Please start a **New Chat** in the sidebar!")
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-message-container'><div class='user-bubble'>{msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-message-container'><div class='ai-avatar'>✦</div><div class='ai-response-body'>{msg['content']}</div></div>", unsafe_allow_html=True)

    if len(st.session_state.messages) < 100:
        active_prompt = st.chat_input("Ask Aether AI anything...")
        if active_prompt:
            if not user_api_key:
                st.error("Please input your Groq API Key in the sidebar.")
            else:
                st.session_state.messages.append({"role": "user", "content": active_prompt})
                cursor.execute("INSERT INTO messages (thread_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                               (st.session_state.current_thread_id, "user", active_prompt, datetime.now()))
                conn.commit()

                with st.spinner("Aether AI is thinking..."):
                    try:
                        res = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                            json={"model": "openai/gpt-oss-120b", "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": active_prompt}]},
                                            headers={"Authorization": f"Bearer {user_api_key}", "Content-Type": "application/json"}, timeout=45)
                        reply = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else f"Error: {res.text}"
                    except Exception as e:
                        reply = f"Connection error: {e}"

                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    cursor.execute("INSERT INTO messages (thread_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                                   (st.session_state.current_thread_id, "assistant", reply, datetime.now()))
                    conn.commit()
                st.rerun()

elif nav_selection == "🎨 Image Studio":
    st.markdown("## 🎨 Image Studio")
    st.markdown("Transform prompts into visual art. **Rule:** Free users get **2 images per day**. Pro users spend **1 token per image**.")
    
    # Check Daily Free Image Limit
    cursor.execute("SELECT image_count, last_image_date FROM users WHERE username=?", (st.session_state.username,))
    row = cursor.fetchone()
    img_count, last_date = row[0], row[1]
    today_str = str(date.today())
    
    if last_date != today_str:
        cursor.execute("UPDATE users SET image_count=0, last_image_date=? WHERE username=?", (today_str, st.session_state.username))
        conn.commit()
        img_count = 0

    img_prompt = st.text_input("✨ Visual Prompt", placeholder="e.g., Ethereal celestial palace...")
    
    # Emoji options for image generation styles
    art_style = st.selectbox("🎭 Art Style Emoji Filter", ["✨ Cosmic & Glowing", "🚀 Cyberpunk Neon", "🌿 Natural & Realistic", "🎨 Anime Fantasy", "💎 Minimalist Vector"])
    
    if st.button("🖼️ Render Artwork", use_container_width=True) and img_prompt:
        can_generate = False
        if st.session_state.tier.startswith("Pro") and st.session_state.tokens > 0:
            st.session_state.tokens -= 1
            cursor.execute("UPDATE users SET tokens=? WHERE username=?", (st.session_state.tokens, st.session_state.username))
            conn.commit()
            can_generate = True
            st.toast("💎 1 Token deducted from Pro balance!")
        elif img_count < 2:
            cursor.execute("UPDATE users SET image_count=? WHERE username=?", (img_count + 1, st.session_state.username))
            conn.commit()
            can_generate = True
            st.toast(f"🎁 Free daily image used ({img_count + 1}/2 today)!")
        else:
            st.error("⚠️ Daily free limit reached (2 images/day) or Pro tokens exhausted! Please top up in **Subscription & Billing**.")

        if can_generate:
            with st.spinner("Rendering artwork canvas..."):
                final_prompt_query = f"{img_prompt} - style {art_style}"
                st.image(f"https://pollinations.ai/p/{final_prompt_query.replace(' ', '%20')}?width=1024&height=1024&nologo=true", caption=img_prompt, use_container_width=True)
                st.success("Visual canvas rendered successfully!")

elif nav_selection == "🛠️ Explore AI Tools":
    st.markdown("## 🛠️ Explore Specialized AI Tools")
    st.info("Select specialized agent workflows configured for advanced productivity.")

elif nav_selection == "📚 Resource Library":
    st.markdown("## 📚 Resource Library & Document Analysis")
    uploaded_file = st.file_uploader("Upload reference document", type=["pdf", "txt", "md"])
    if uploaded_file:
        st.success(f"Successfully indexed '{uploaded_file.name}' into the Resource Library!")

elif nav_selection == "📂 Projects":
    st.markdown("## 📂 Project Workspaces")
    p_name = st.text_input("Project Codename")
    if st.button("Initialize Workspace") and p_name:
        cursor.execute("INSERT OR REPLACE INTO projects VALUES (?, ?)", (p_name, "Custom directives"))
        conn.commit()
        st.success(f"Project workspace '{p_name}' initialized!")

elif nav_selection == "💳 Subscription & Billing":
    st.markdown("## 💳 Subscription & Billing")
    st.markdown(f"**Current Tier:** {st.session_state.tier}")
    st.markdown(f"**Available Tokens:** {st.session_state.tokens} tokens")
    
    st.markdown("""
        ### 🌟 Pro Subscription Plan (1 Month = 300 Tokens)
        * **Price:** NPR 500 / month
        * **Benefits:** 300 Image Generation Tokens (1 token = 1 image), priority access, and expanded limits.
        * **Free Tier Perks:** 2 free images per day + 100 messages per chat thread.
    """)
    
    # Display Dad's eSewa QR Code
    try:
        st.image("payment_qr.png", caption="Scan via eSewa (Dammar Singh Saud / @dammarsaud)", width=280)
    except Exception:
        st.info("💡 Place your dad's eSewa QR image as `payment_qr.png` in your GitHub repository folder.")

    st.markdown("""
    **How to Upgrade:**
    1. Scan the eSewa QR code above and pay **NPR 500**.
    2. Write your username (**""" + st.session_state.username + """**) in payment remarks.
    3. Enter the VIP Access Code below to get your **300 tokens** instantly:
    """)
    
    entered_code = st.text_input("Enter VIP Access Code", type="password")
    if st.button("Activate Pro Subscription (300 Tokens)"):
        if entered_code == "AETHER2026VIP":
            cursor.execute("UPDATE users SET tier='Pro (1 Month)', tokens=tokens+300 WHERE username=?", (st.session_state.username,))
            conn.commit()
            st.session_state.tier = "Pro (1 Month)"
            st.session_state.tokens += 300
            st.success("🎉 Pro subscription activated! 300 tokens added to your account!")
            st.rerun()
        else:
            st.error("Invalid VIP Access Code.")

elif nav_selection == "⚙️ Settings":
    st.markdown("## ⚙️ Platform Settings")
    selected_theme = st.selectbox("Theme Mode", ["Light", "Dark"], index=0 if st.session_state.theme == "Light" else 1)
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()
    if st.button("Purge Complete History"):
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM threads")
        conn.commit()
        st.success("History purged.")
        st.rerun()