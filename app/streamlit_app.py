"""Interface web d'AssurIA.

python -m streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from common.assistant import AssurIA, build_tools  # noqa: E402
from common.config import CHAT_MODEL, DATA, env, estimate_cost, get_openai_client  # noqa: E402

st.set_page_config(page_title="AssurIA — Kéné Assurances IARD")
st.title("AssurIA")
st.caption("Assistant de Kéné Assurances IARD (compagnie fictive). Tarifs indicatifs : "
           "seule une offre écrite engage la compagnie.")

with st.sidebar:
    st.header("Outils")
    use_rag = st.toggle("Documents (file_search)", value=True, disabled=not env("VECTOR_STORE_ID"))
    use_functions = st.toggle("Prime et sinistres (function)", value=True)
    use_code = st.toggle("Analyse sinistres 2025 (code_interpreter)", value=False)
    use_web = st.toggle("Recherche web (web_search)", value=False)
    temperature = st.slider("Température", 0.0, 1.0, 0.2, 0.1)
    st.caption(f"Modèle : {CHAT_MODEL}")
    if not env("VECTOR_STORE_ID"):
        st.warning("VECTOR_STORE_ID vide : lancer python -m m4_tools.setup_vector_store")
    if st.button("Nouvelle conversation"):
        st.session_state.pop("bot", None)
        st.session_state.messages = []

config = (use_rag, use_functions, use_code, use_web, temperature)
if st.session_state.get("config") != config:
    file_ids = []
    if use_code:
        if "csv_file_id" not in st.session_state:
            with (DATA / "sinistres_2025.csv").open("rb") as f:
                st.session_state.csv_file_id = get_openai_client().files.create(file=f, purpose="assistants").id
        file_ids = [st.session_state.csv_file_id]
    bot = AssurIA(temperature=temperature,
                  tools=build_tools(file_search=use_rag, functions=use_functions,
                                    code_interpreter=use_code, web_search=use_web, code_file_ids=file_ids))
    if "bot" in st.session_state:  # changer d'outils ne coupe pas la conversation
        bot.previous_response_id = st.session_state.bot.previous_response_id
    st.session_state.bot, st.session_state.config = bot, config

st.session_state.setdefault("messages", [])
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for img in msg.get("images", []):
            st.image(img)
        if msg.get("meta"):
            st.caption(msg["meta"])

if prompt := st.chat_input("Garanties, devis auto, suivi de sinistre…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("…"):
            turn = st.session_state.bot.ask(prompt)
        st.markdown(turn.text)
        images = [f for f in turn.files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        for img in images:
            st.image(img)
        parts = []
        if turn.citations:
            parts.append("Sources : " + ", ".join(turn.citations))
        if turn.tool_calls:
            parts.append("Outils : " + ", ".join(t.split("(")[0] for t in turn.tool_calls))
        cost = estimate_cost(CHAT_MODEL, turn.input_tokens, turn.output_tokens)
        parts.append(f"{turn.input_tokens} / {turn.output_tokens} jetons · ≈ {cost:.4f} $ · {turn.latency_s} s")
        if turn.blocked:
            parts.append("Bloqué par le garde-fou")
        meta = " · ".join(parts)
        st.caption(meta)
    st.session_state.messages.append({"role": "assistant", "content": turn.text,
                                      "images": images, "meta": meta})
