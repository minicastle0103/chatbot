import base64
from pathlib import Path
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
from transformers import logging

logging.set_verbosity_error()

from chatbot.chatbot import render_chatbot

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
IMAGE_DIR = ROOT_DIR / "base_image"
BOT_ICON_PATH = IMAGE_DIR / "bot_logo.png"
BG_IMAGE_PATH = IMAGE_DIR / "fab.mp4"
LOGOW_PATH = IMAGE_DIR / "logo.png"
HIT_PATH = IMAGE_DIR / "title.png"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "홈 (메인보드)"

try:
    if BOT_ICON_PATH.exists():
        fav_icon = Image.open(BOT_ICON_PATH)
    else:
        fav_icon = "🧩"
except Exception:
    fav_icon = "🧩"

st.set_page_config(
    page_title="SK Chat Bot",
    page_icon=fav_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_app_css = "background-color: #F8F9FA;"

if BG_IMAGE_PATH.exists() and st.session_state.current_menu == "홈 (메인보드)":
    bg_app_css = "background: transparent !important;"
    vid_b64 = get_base64_of_bin_file(BG_IMAGE_PATH)
    st.markdown(
        f"""
        <style>
        #bg-video {{
            position: fixed; top: 0; left: 0; min-width: 100vw; min-height: 100vh;
            z-index: -100; object-fit: cover;
        }}
        </style>
        <video autoplay loop muted playsinline id="bg-video">
            <source src="data:video/mp4;base64,{vid_b64}" type="video/mp4">
        </video>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
        f"""
        <style>
        #bg-video {{
            position: fixed; top: 0; left: 0; min-width: 100vw; min-height: 100vh;
            z-index: -100; object-fit: cover;
        }}
        .stApp {{ {bg_app_css} }}
        header {{ background: transparent !important; }}
        #MainMenu {{ visibility: hidden !important; }}
        html, body, [data-testid="stWidgetLabel"], .stMarkdown {{
            color: #000000 !important;
        }}
        .stCaption {{ color: #666666 !important; }}
        .logo-container {{ position: absolute; top: -40px; right: 10px; }}
        .stTextArea textarea {{
            background-color: #FFFFFF; color: #000000 !important;
            border-radius: 8px; caret-color: #000000 !important;
        }}
        .stTextArea textarea::placeholder {{
            color: #000000 !important; opacity: 0.7 !important;
        }}
        
        /* 1. 선택되지 않은 기본 메뉴 버튼 (Secondary) */
        div[data-testid="stButton"] > button[kind="secondary"] {{
            background-color: #2B2B2B !important; color: #ffffff !important;
            border-radius: 12px !important; border: none !important;
            height: 50px !important; max-width: 600px !important;
            font-weight: 500 !important; transition: all 0.3s ease !important;
            white-space: normal !important; word-wrap: break-word !important;
        }}
        /* 기본 메뉴에 마우스 올렸을 때: 빨간색 */
        div[data-testid="stButton"] > button[kind="secondary"]:hover {{
            background-color: #EA002C !important; transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        /* 기본 메뉴를 클릭하는 순간: 주황색 */
        div[data-testid="stButton"] > button[kind="secondary"]:active {{
            background-color: #F47725 !important;
        }}

        /* 2. 클릭 후 선택이 유지되는 메뉴 버튼 (Primary) */
        div[data-testid="stButton"] > button[kind="primary"] {{
            background-color: #F47725 !important; color: #FFFFFF !important;
            border-radius: 10px !important; border: none !important;
            height: 50px !important; font-weight: bold !important;
            font-size: 1.1rem !important; transition: all 0.3s ease !important;
        }}
        /* 선택된 메뉴에 마우스 올렸을 때: 주황색 유지 */
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background-color: #F47725 !important; transform: translateY(-2px);
        }}
        /* 선택된 메뉴를 클릭할 때: 주황색 유지 */
        div[data-testid="stButton"] > button[kind="primary"]:active {{
            background-color: #F47725 !important;
        }}

        div[data-testid="collapsedControl"],
        div[data-testid="collapsedControl"] svg,
        div[data-testid="stSidebarCollapseButton"],
        div[data-testid="stSidebarCollapseButton"] svg {{
            color: #EB0029 !important; fill: #EB0029 !important;
        }}
        div[data-testid="collapsedControl"]:hover svg,
        div[data-testid="stSidebarCollapseButton"]:hover svg {{
            fill: #EA002C !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #1E1F20;
        }}
        [data-testid="stSpinner"] p {{
            color: #000000 !important;
            font-weight: bold !important;
        }}
        [data-testid="stSpinner"] svg circle {{
            stroke: #000000 !important;
        }}
        div[data-testid="stPopoverBody"] [data-testid="stSpinner"] p {{
            color: #000000 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

with st.sidebar:
    st.markdown(
        "<div style='font-weight: 600; margin-bottom: 0px; "
        "font-size: 30px; color: #ffffff;'>메뉴</div>",
        unsafe_allow_html=True
    )
    st.write("---")

    m_chat = "Chat Bot"
    if st.button(
        m_chat, use_container_width=True,
        type="primary" if st.session_state.current_menu == m_chat
        else "secondary"
    ):
        st.session_state.current_menu = m_chat
        st.rerun()

if st.session_state.current_menu == "홈 (메인보드)":
    if LOGOW_PATH.exists():
        img_base64 = get_base64_of_bin_file(LOGOW_PATH)
        st.markdown(
            f'<div class="logo-container">'
            f'<img src="data:image/png;base64,{img_base64}" width="150">'
            f'</div>',
            unsafe_allow_html=True
        )

    if HIT_PATH.exists():
        img_base64 = get_base64_of_bin_file(HIT_PATH)
        st.markdown(
            f'<div style="position: absolute; top: -10px; left: 30px;">'
            f'<img src="data:image/png;base64,{img_base64}" style="width: 800px;">'
            f"</div>",
            unsafe_allow_html=True,
        )

elif st.session_state.current_menu == "Chat Bot":
    render_chatbot(ROOT_DIR, get_base64_of_bin_file)

components.html(
    """
    <script>
    const doc = window.parent.document;
    setInterval(() => {
        const textareas = doc.querySelectorAll('textarea');
        textareas.forEach(ta => {
            if (!ta.dataset.enterBound) {
                ta.dataset.enterBound = 'true';
                ta.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault(); e.stopPropagation();
                        ta.blur();
                        setTimeout(() => {
                            const btns = Array.from(
                                doc.querySelectorAll('button')
                            );
                            const sBtn = btns.find(
                                b => b.innerText.includes('질문하기')
                            );
                            if (sBtn) sBtn.click();
                        }, 50);
                    }
                }, { capture: true });
            }
        });
    }, 500);
    </script>
    """,
    height=0, width=0,
)