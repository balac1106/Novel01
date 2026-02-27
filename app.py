# -*- coding: utf-8 -*-
"""
視覺小說式互動創作介面
結合故事歷史、動作指令與狀態追蹤，組合成發送給 AI 的 Prompt。
"""

import re
import streamlit as st
from config.prompts import (
    SYSTEM_INSTRUCTION,
    ACTION_MATRIX,
    ACTION_GROUPS,
    DEFAULT_STATE,
)

# ----- 頁面設定 -----
st.set_page_config(
    page_title="互動小說創作",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----- 自訂樣式（視覺小說風格）-----
st.markdown("""
<style>
    /* 主敘事區：深色底、暖色字 */
    .stTextArea textarea {
        background-color: #1a1625 !important;
        color: #e8dcd0 !important;
        border: 1px solid #3d3548;
        border-radius: 8px;
        font-size: 1rem;
        line-height: 1.7;
    }
    /* 狀態面板 */
    .state-panel {
        background: linear-gradient(135deg, #2d2640 0%, #1e1a2e 100%);
        border: 1px solid #4a4058;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        color: #c9bfb5;
        font-size: 0.9rem;
    }
    .state-panel h4 { color: #d4a574; margin-bottom: 0.5rem; }
    /* 按鈕區塊標題 */
    .action-group-title {
        color: #b8a090;
        font-weight: 600;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #3d3548;
    }
    /* 敘事輸出區 */
    .narrative-box {
        background: #1a1625;
        border: 1px solid #3d3548;
        border-radius: 10px;
        padding: 1.5rem;
        min-height: 200px;
        color: #e8dcd0;
        line-height: 1.8;
        white-space: pre-wrap;
    }
    /* 隱藏 Streamlit 預設的 padding */
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化 session state：故事歷史與狀態追蹤"""
    if "story_history" not in st.session_state:
        st.session_state.story_history = []  # [{"role": "user"|"assistant", "content": "..."}]
    if "current_state" not in st.session_state:
        st.session_state.current_state = DEFAULT_STATE.copy()
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = ""


def parse_state_from_response(text: str) -> dict:
    """從 AI 回覆中解析 【狀態】 區塊，更新狀態字典"""
    state = st.session_state.current_state.copy()
    pattern = r"【狀態】\s*\n(.*?)---"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return state
    block = match.group(1).strip()
    for line in block.split("\n"):
        line = line.strip()
        if "：" in line or ":" in line:
            sep = "：" if "：" in line else ":"
            key, _, value = line.partition(sep)
            key = key.strip()
            value = value.strip()
            if key in state:
                state[key] = value
    return state


def build_full_prompt(instruction: str) -> str:
    """組合：系統指令 + 故事歷史 + 當前狀態 + 本次動作指令"""
    state = st.session_state.current_state
    state_block = "\n".join(f"- {k}：{v}" for k, v in state.items())

    user_messages = []
    for msg in st.session_state.story_history:
        if msg["role"] == "user":
            user_messages.append(f"[使用者指令] {msg['content']}")
        else:
            user_messages.append(f"[AI 敘事]\n{msg['content']}")

    history_text = "\n\n---\n\n".join(user_messages) if user_messages else "（尚無歷史，請從第一個動作開始。）"

    full = f"""【系統指令】
{SYSTEM_INSTRUCTION}

【當前狀態】
{state_block}

【故事歷史】
{history_text}

【本次使用者動作指令】
{instruction}

請根據以上，寫出一段符合風格基因的敘事，並在文末以固定格式回傳狀態。"""
    return full


def on_action_click(action_id: str):
    """按下動作按鈕：寫入歷史、建 Prompt、可選呼叫 API"""
    instruction = ACTION_MATRIX.get(action_id, "")
    if not instruction:
        return

    # 將「使用者選擇的動作」加入歷史（作為 user 訊息）
    st.session_state.story_history.append({"role": "user", "content": f"[{action_id}] {instruction}"})

    prompt = build_full_prompt(instruction)
    st.session_state.last_prompt = prompt

    # 若側邊欄有設定 API key，則呼叫 OpenAI
    api_key = st.session_state.get("openai_api_key", "").strip()
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=st.session_state.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
            )
            assistant_text = response.choices[0].message.content or ""
            st.session_state.story_history.append({"role": "assistant", "content": assistant_text})
            new_state = parse_state_from_response(assistant_text)
            st.session_state.current_state.update(new_state)
        except Exception as e:
            st.error(f"API 呼叫失敗：{e}")
    else:
        # 未設定 API key：只更新 last_prompt，供使用者複製或手動貼到其他 AI
        st.info("已組合 Prompt。請在側邊欄輸入 OpenAI API Key 以自動取得 AI 回覆，或展開下方「生成的 Prompt」複製到其他介面。")
    st.rerun()


# ----- 初始化 -----
init_session_state()

# ----- 側邊欄：API 與狀態 -----
with st.sidebar:
    st.header("⚙️ 設定與狀態")

    st.subheader("API（選填）")
    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.get("openai_api_key", ""),
        type="password",
        key="openai_api_key",
        help="填入後，按動作按鈕會自動呼叫 API 並顯示 AI 敘事。",
    )
    model = st.selectbox(
        "模型",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        index=0,
        key="model",
    )

    st.subheader("📋 當前狀態")
    for k, v in st.session_state.current_state.items():
        st.markdown(f"**{k}**：{v}")

    if st.button("🔄 重置狀態與歷史", use_container_width=True):
        st.session_state.story_history = []
        st.session_state.current_state = DEFAULT_STATE.copy()
        st.session_state.last_prompt = ""
        st.rerun()

# ----- 主區：標題與敘事區 -----
st.title("📖 互動小說創作")
st.caption("選擇下方動作按鈕，程式會將「故事歷史 + 動作指令 + 狀態」組合成 Prompt 並可選擇呼叫 AI。")

# 顯示最新一段 AI 敘事（若有的話）
last_assistant = None
for msg in reversed(st.session_state.story_history):
    if msg["role"] == "assistant":
        last_assistant = msg["content"]
        break

if last_assistant:
    # 可選擇只顯示敘事本文（去掉狀態區塊）給閱讀用
    display_text = re.sub(r"\n---\s*\n【狀態】.*?---", "\n", last_assistant, flags=re.DOTALL).strip()
    st.markdown('<div class="narrative-box">' + display_text.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="narrative-box">（尚未產生敘事。請從下方選擇一個動作開始。）</div>',
        unsafe_allow_html=True,
    )

# ----- 動作按鈕區（動作矩陣）-----
st.markdown("---")
st.subheader("動作指令")

for group in ACTION_GROUPS:
    st.markdown(f'<p class="action-group-title">{group["label"]}</p>', unsafe_allow_html=True)
    cols = st.columns(min(len(group["actions"]), 4))
    for i, action_id in enumerate(group["actions"]):
        with cols[i % len(cols)]:
            if st.button(action_id, key=f"btn_{action_id}", use_container_width=True):
                on_action_click(action_id)

# ----- 可展開：生成的 Prompt -----
with st.expander("📄 查看／複製「生成的 Prompt」"):
    if st.session_state.last_prompt:
        st.text_area("Prompt（可複製）", value=st.session_state.last_prompt, height=300, disabled=False)
    else:
        st.info("按下任一動作按鈕後，這裡會顯示組合好的完整 Prompt。")

# ----- 完整歷史（可選展開）-----
with st.expander("📜 完整對話歷史"):
    if st.session_state.story_history:
        for i, msg in enumerate(st.session_state.story_history):
            role = "使用者指令" if msg["role"] == "user" else "AI 敘事"
            st.markdown(f"**[{i+1}] {role}**")
            st.text(msg["content"][:500] + ("..." if len(msg["content"]) > 500 else ""))
            st.markdown("---")
    else:
        st.caption("尚無歷史。")
