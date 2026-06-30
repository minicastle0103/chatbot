import os
import time
import streamlit as st

from .ingest import build_vector_db
from .rag import ask_truss_bot

def render_chatbot(root_dir, get_base64_func):
    image_dir = root_dir / "base_image"
    docs_dir = root_dir / "data" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    logo_path = image_dir / "logo.png"
    hi_path = image_dir / "hitruss.png"
    bot_icon_path = image_dir / "bot_logo.png"

    if logo_path.exists():
        img_base64 = get_base64_func(logo_path)
        st.markdown(
            f'<div class="logo-container">'
            f'<img src="data:image/png;base64,{img_base64}" width="150">'
            f'</div>',
            unsafe_allow_html=True
        )

    if hi_path.exists():
        img_base64 = get_base64_func(hi_path)
        st.markdown(
            f'<div style="text-align: left; margin-top: -80px; '
            f'margin-bottom: -10px;">'
            f'<img src="data:image/png;base64,{img_base64}" '
            f'width="250" class="refresh-logo"></a></div>',
            unsafe_allow_html=True
        )

    if st.button("홈 화면으로 돌아가기", key="btn_back_home_chat"):
        st.session_state.current_menu = "홈 (메인보드)"
        st.session_state.messages = []
        st.session_state.input_key = 0
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    model_options = {
        "Qwen 2.5 (로컬)": "qwen2.5",
        "Llama 3.1 (로컬)": "llama-3.1",
        "사내망 API": "internal"
    }

    _, model_col = st.columns([5, 1])
    with model_col:
        selected_model_label = st.selectbox(
            "응답 모델 선택",
            list(model_options.keys()),
            index=0,
            label_visibility="collapsed"
        )
    selected_model_id = model_options[selected_model_label]

    chat_container = st.container(height=680, border=False)
    clicked_example = None

    with chat_container:
        if len(st.session_state.messages) == 0:
            title_style = (
                "font-size: 2.5rem; font-weight: 700; "
                "background: linear-gradient(90deg, #00E600, #00AD1D, "
                "#003087); -webkit-background-clip: text; "
                "-webkit-text-fill-color: transparent; "
                "display: inline-block;"
            )

            user_name = "사용자"
            st.markdown(
                f'<div style="margin-top: 400px; padding-bottom: 20px;">'
                f'<div style="font-size: 1.5rem; font-weight: 600; '
                f'color: #5F6368;">{user_name}님, 안녕하세요</div>'
                f'<div style="{title_style}">무엇을 도와드릴까요?</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                "<div style='color: #000000; font-size: 1.1rem; "
                "margin-bottom: 10px;'>💡 제안하는 질문</div>",
                unsafe_allow_html=True
            )
            left_spacer, right_spacer = st.columns([1, 1])

            with left_spacer:
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    btn1 = "반도체 Value Chain"
                    if st.button(btn1, use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "반도체 Value Chain에 대해 설명해 주세요."
                        })
                        st.rerun()
                    btn2 = "DRAM vs NAND Flsh"
                    if st.button(btn2, use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "DRAM과 NAND Flash의 차이점에 대해 설명해 주세요."
                        })
                        st.rerun()
                with sub_col2:
                    btn3 = "CMP공정의 이유"
                    if st.button(btn3, use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "CMP공정은 무엇이고, CMP공정이 중요한 이유는 무엇인가요?"
                        })
                        st.rerun()
                    btn4 = "ALD?"
                    if st.button(btn4, use_container_width=True):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "ALD는 무엇인가요?"
                        })
                        st.rerun()
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    user_svg = (
                        "data:image/svg+xml;utf8,"
                        "<svg xmlns='http://www.w3.org/2000/svg' "
                        "viewBox='0 0 24 24' fill='black'>"
                        "<path d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4"
                        "-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 "
                        "4v2h16v-2c0-2.66-5.33-4-8-4z'/></svg>"
                    )
                    with st.chat_message("user", avatar=user_svg):
                        st.markdown(msg["content"])

                elif msg["role"] == "assistant":
                    avatar_icon = (
                        str(bot_icon_path) if bot_icon_path.exists()
                        else "🤖"
                    )
                    with st.chat_message("assistant", avatar=avatar_icon):
                        st.markdown(msg["content"])
                        if msg.get("sources"):
                            for s in msg["sources"]:
                                st.caption(f"- {s}")
                        img_data = msg.get("image")
                        if isinstance(img_data, list) and len(img_data) > 0:
                            img_path = img_data[0]
                        else:
                            img_path = img_data

                        if isinstance(img_path, str):
                            if os.path.exists(img_path):
                                st.image(
                                    msg["image"],
                                    caption="관련 참고 자료",
                                    width=600
                                )

    st.write("")
    btn_col, input_col = st.columns([1, 15])

    with btn_col:
        with st.popover("＋", use_container_width=True):
            st.markdown(
                "<div style='font-weight: 600; margin-bottom: 5px; "
                "color: #000000;'>📂 문서 업로드</div>",
                unsafe_allow_html=True
            )
            uploaded_files = st.file_uploader(
                "문서 업로드",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )

            if st.button("저장 및 분석 실행", use_container_width=True):
                if uploaded_files:
                    for f in uploaded_files:
                        with open(docs_dir / f.name, "wb") as save_f:
                            save_f.write(f.read())
                    with st.spinner("문서를 학습하는 중..."):
                        build_vector_db()
                        st.success("학습 완료!")
                        time.sleep(0.5)
                        st.rerun()

            st.divider()
            st.markdown(
                "<div style='font-weight: 600; margin-bottom: 5px; "
                "color: #000000;'>🗑️ 문서 관리 및 삭제</div>",
                unsafe_allow_html=True
            )
            saved_files = [f.name for f in docs_dir.iterdir() if f.is_file()]

            if saved_files:
                files_to_delete = st.multiselect(
                    "삭제할 파일을 선택하세요",
                    saved_files,
                    label_visibility="collapsed"
                )
                btn_del = "선택 삭제 및 DB 갱신"
                if st.button(
                    btn_del,
                    use_container_width=True,
                    type="primary"
                ):
                    if files_to_delete:
                        for f_name in files_to_delete:
                            file_path = docs_dir / f_name
                            if file_path.exists():
                                file_path.unlink()
                        with st.spinner("문서 DB 갱신 중..."):
                            build_vector_db()
                        st.success("삭제 및 갱신 완료!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("삭제할 파일을 먼저 선택해주세요.")
            else:
                st.caption("현재 서버에 저장된 문서가 없습니다.")

    with input_col:
        user_question = st.text_area(
            "질문 입력",
            height=70,
            label_visibility="collapsed",
            placeholder="질문을 입력하세요...",
            key=f"text_input_{st.session_state.input_key}"
        )

    _, col_btn = st.columns([14, 2])
    with col_btn:
        submit_clicked = st.button(
            "질문하기", type="primary", use_container_width=True
        )

    final_question = clicked_example if clicked_example else user_question

    if (submit_clicked or clicked_example) and final_question.strip():
        if len(st.session_state.messages) > 10:
            st.session_state.messages = st.session_state.messages[-6:]

        st.session_state.messages.append({
            "role": "user",
            "content": final_question
        })
        st.session_state.input_key += 1
        st.rerun()

    if (st.session_state.messages and
            st.session_state.messages[-1]["role"] == "user"):
        last_question = st.session_state.messages[-1]["content"]
        with st.spinner(
            f"[{selected_model_label}] 답변 생성 중..."
        ):
            try:
                answer, sources, matched_image = ask_truss_bot(
                    last_question, selected_model_id
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "image": matched_image
                })
                st.rerun()
            except Exception as e:
                st.error(f"오류 발생: {e}")