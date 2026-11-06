"""Interface web d'AssurIA.

python -m streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from common.assistant import AssurIA, build_tools  # noqa: E402
from common.config import CHAT_MODEL, DATA, env, estimate_cost, get_openai_client  # noqa: E402

ASSISTANT_AVATAR = ":material/shield_person:"

QUICK_ACTIONS = {
    "devis": (":material/directions_car:", "Devis auto instantané", "Je veux un devis pour mon assurance auto."),
    "sinistre": (":material/pending_actions:", "Suivre un sinistre", "Où en est mon dossier SIN-2026-0101 ?"),
    "garanties": (":material/verified_user:", "Mes garanties", "Quelles garanties contient la formule Tiers étendu ?"),
    "declarer": (":material/car_crash:", "Déclarer un accident", "J'ai eu un accident de voiture, que dois-je faire ?"),
}

st.set_page_config(page_title="AssurIA — Kéné Assurances IARD", page_icon=":material/shield_person:",
                   layout="centered", initial_sidebar_state="collapsed")
st.markdown(f"<style>{(Path(__file__).parent / 'style.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Paramètres")
    use_rag = st.toggle("Documents (file_search)", value=True, disabled=not env("VECTOR_STORE_ID"))
    use_functions = st.toggle("Prime et sinistres (function)", value=True)
    use_code = st.toggle("Analyse sinistres 2025 (code_interpreter)", value=False)
    use_web = st.toggle("Recherche web (web_search)", value=False)
    temperature = st.slider("Température", 0.0, 1.0, 0.2, 0.1)
    st.caption(f"Modèle : {CHAT_MODEL}")
    if not env("VECTOR_STORE_ID"):
        st.warning("VECTOR_STORE_ID vide : lancer python -m m4_tools.setup_vector_store")
    if st.button("Nouvelle conversation", icon=":material/add_comment:", use_container_width=True):
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

def quick_action(slot, key: str) -> None:
    icon, label, prompt = QUICK_ACTIONS[key]
    if slot.button(label, icon=icon, key=f"qa-{key}", use_container_width=True):
        st.session_state.pending_prompt = prompt
        st.rerun()


def landing() -> None:
    st.markdown("""
<div class="hero">
  <div class="hero-top">
    <span class="hero-brand">KÉNÉ ASSURANCES</span>
    <span class="hero-badge"><i></i>AssurIA en ligne</span>
  </div>
  <h1>Protéger ce qui compte, <span class="accent">en une question.</span></h1>
  <p>Devis, garanties, sinistres : des réponses tirées des conditions de la compagnie.</p>
</div>
<p class="section-label">Que souhaitez-vous faire ?</p>""", unsafe_allow_html=True)

    with st.container(key="quick"):
        quick_action(st, "devis")
        left, right = st.columns(2)
        quick_action(left, "sinistre")
        quick_action(right, "garanties")
        quick_action(st, "declarer")

    st.markdown("""
<div class="trust"><span>Réponses sourcées</span><span>Primes calculées sur le barème</span><span>Données confidentielles</span></div>
<p class="legal">Kéné Assurances IARD est une compagnie fictive. Tarifs indicatifs : seule une offre écrite engage la compagnie.</p>""",
                unsafe_allow_html=True)


def chat_header() -> None:
    st.markdown("""
<div class="chat-head">
  <div class="mark">A</div>
  <div><div class="name">AssurIA</div><div class="sub">Kéné Assurances IARD</div></div>
</div>""", unsafe_allow_html=True)


def render_meta(turn) -> str:
    parts = []
    if turn.citations:
        parts.append("Sources : " + ", ".join(turn.citations))
    if turn.tool_calls:
        parts.append("Outils : " + ", ".join(t.split("(")[0] for t in turn.tool_calls))
    cost = estimate_cost(CHAT_MODEL, turn.input_tokens, turn.output_tokens)
    parts.append(f"{turn.input_tokens} / {turn.output_tokens} jetons · ≈ {cost:.4f} $ · {turn.latency_s} s")
    if turn.blocked:
        parts.append("Bloqué par le garde-fou")
    return " · ".join(parts)


if not st.session_state.messages and "pending_prompt" not in st.session_state:
    landing()
else:
    chat_header()

for msg in st.session_state.messages:
    avatar = ASSISTANT_AVATAR if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        for img in msg.get("images", []):
            st.image(img)
        if msg.get("meta"):
            st.caption(msg["meta"])

prompt = st.chat_input("Écrire à AssurIA…")
prompt = prompt or st.session_state.pop("pending_prompt", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("Recherche dans les documents…"):
            turn = st.session_state.bot.ask(prompt)
        st.markdown(turn.text)
        images = [f for f in turn.files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        for img in images:
            st.image(img)
        meta = render_meta(turn)
        st.caption(meta)
    st.session_state.messages.append({"role": "assistant", "content": turn.text,
                                      "images": images, "meta": meta})
