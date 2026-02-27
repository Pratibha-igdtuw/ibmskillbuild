import os

from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from PIL import Image


load_dotenv()

st.set_page_config(page_title="AI Health Companion", layout="wide")

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.title("AI Health Companion")
    st.error("Missing API key. Set GOOGLE_API_KEY or GEMINI_API_KEY in your environment.")
    st.stop()

genai.configure(api_key=API_KEY)

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Space+Grotesk:wght@400;600;700&display=swap');

:root {
    --bg-start: #f6f1e7;
    --bg-end: #efe6d6;
    --text: #1f2933;
    --muted: #5b616a;
    --card: #ffffff;
    --accent: #0f766e;
    --accent-strong: #0b5f59;
    --border: #e3d8c7;
    --shadow: 0 12px 28px rgba(31, 41, 51, 0.12);
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', 'Trebuchet MS', sans-serif;
    color: var(--text);
}

h1, h2, h3 {
    font-family: 'DM Serif Display', 'Georgia', serif;
    letter-spacing: 0.3px;
    color: var(--text);
}

.stApp {
    background: radial-gradient(circle at top, var(--bg-start), var(--bg-end));
}

.main .block-container {
    max-width: 1150px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

.hc-hero {
    display: grid;
    grid-template-columns: 2.2fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}

.hc-hero-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
}

.hc-chip {
    display: inline-block;
    background: #fff1d0;
    color: #7a4a00;
    border: 1px solid #f1d3a3;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
}

.hc-subtitle {
    font-size: 1.05rem;
    color: var(--muted);
    margin-top: 0.5rem;
}

.hc-list {
    margin: 0.8rem 0 0;
    padding-left: 1.2rem;
    color: var(--muted);
}

.hc-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.75rem;
}

.stTabs [data-baseweb="tab"] {
    background: #f7efe1;
    border-radius: 999px;
    padding: 0.45rem 1rem;
    border: 1px solid var(--border);
}

.stTabs [aria-selected="true"] {
    background: var(--accent);
    color: #ffffff;
    border-color: var(--accent);
}

div.stButton > button,
div.stDownloadButton > button {
    background: var(--accent);
    color: #ffffff;
    border-radius: 10px;
    border: none;
    padding: 0.55rem 1.1rem;
    box-shadow: 0 10px 20px rgba(15, 118, 110, 0.2);
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    background: var(--accent-strong);
    transform: translateY(-1px);
}

div.stButton > button:active,
div.stDownloadButton > button:active {
    transform: translateY(0);
}

.stProgress > div > div {
    background: var(--accent);
}

.stCaption {
    color: var(--muted);
}

@media (max-width: 900px) {
    .hc-hero {
        grid-template-columns: 1fr;
    }
}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


def pick_model(preferred):
    try:
        models = genai.list_models()
    except Exception:
        return preferred, None

    supported = [
        model.name.replace("models/", "")
        for model in models
        if "generateContent" in model.supported_generation_methods
    ]

    if preferred in supported:
        return preferred, None

    if supported:
        fallback = supported[0]
        message = f"Preferred model '{preferred}' not available. Using '{fallback}'."
        return fallback, message

    return preferred, None


PREFERRED_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MODEL_NAME, MODEL_WARNING = pick_model(PREFERRED_MODEL)
MODEL = genai.GenerativeModel(MODEL_NAME)


DEFAULT_PROFILE = {
    "goals": "Lose 10 pounds in 3 months\nImprove cardiovascular health",
    "conditions": "None",
    "routines": "30-minute walk 3x/week",
    "preferences": "Vegetarian\nLow carb",
    "restrictions": "No dairy\nNo nuts",
}

if "health_profile" not in st.session_state:
    st.session_state.health_profile = DEFAULT_PROFILE.copy()


def profile_completion(profile):
    filled = sum(1 for value in profile.values() if str(value).strip())
    total = len(profile)
    return int((filled / total) * 100)


def get_gemini_response(input_prompt, image_data=None):
    content = [input_prompt]
    if image_data:
        content.extend(image_data)

    try:
        response = MODEL.generate_content(content)
        return response.text.strip()
    except Exception as exc:
        message = str(exc)
        if "not found" in message or "404" in message:
            message += " Try setting GEMINI_MODEL to an available model."
        st.error(f"AI error: {message}")
        return ""


def input_image_setup(uploaded_file):
    if uploaded_file is None:
        return None
    bytes_data = uploaded_file.getvalue()
    return [{"mime_type": uploaded_file.type, "data": bytes_data}]


def show_response(title, text):
    if text:
        st.subheader(title)
        st.markdown(text)


if MODEL_WARNING:
    st.warning(MODEL_WARNING)

st.markdown(
    """
    <div class="hc-hero">
        <div class="hc-hero-card">
            <div class="hc-chip">Student health guide</div>
            <h1>AI Health Companion</h1>
            <p class="hc-subtitle">
                Simple, personalized guidance for meals, food analysis, and health questions.
            </p>
            <ul class="hc-list">
                <li>Build meal plans that fit your routine.</li>
                <li>Analyze food photos for quick nutrition clues.</li>
                <li>Ask clear, beginner-friendly health questions.</li>
            </ul>
        </div>
        <div class="hc-hero-card">
            <h3>Quick Start</h3>
            <p>1) Fill your profile in the sidebar.</p>
            <p>2) Pick a tab and generate results.</p>
            <p>3) Download your meal plan if needed.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

hero_image_path = os.path.join(os.path.dirname(__file__), "OIP.jpg")
if os.path.exists(hero_image_path):
    st.image(hero_image_path, use_column_width=True, caption="Healthy meal inspiration")
else:
    st.info("Add OIP.jpg in the project folder to display the hero image.")

with st.sidebar:
    st.header("Your Health Profile")
    st.caption("Update this once to improve all results.")

    with st.form("profile_form"):
        health_goals = st.text_area(
            "Health goals",
            value=st.session_state.health_profile["goals"],
            placeholder="Example: Build stamina, lose 2 kg in 2 months",
        )
        medical_conditions = st.text_area(
            "Medical conditions",
            value=st.session_state.health_profile["conditions"],
            placeholder="Example: None, PCOS, diabetes",
        )
        fitness_routines = st.text_area(
            "Fitness routines",
            value=st.session_state.health_profile["routines"],
            placeholder="Example: 30-minute walk 3x/week",
        )
        food_preferences = st.text_area(
            "Food preferences",
            value=st.session_state.health_profile["preferences"],
            placeholder="Example: Vegetarian, low spice",
        )
        restrictions = st.text_area(
            "Dietary restrictions",
            value=st.session_state.health_profile["restrictions"],
            placeholder="Example: No dairy, peanut allergy",
        )

        submitted = st.form_submit_button("Save Profile")

    if submitted:
        st.session_state.health_profile = {
            "goals": health_goals,
            "conditions": medical_conditions,
            "routines": fitness_routines,
            "preferences": food_preferences,
            "restrictions": restrictions,
        }
        st.success("Profile updated.")

    completion = profile_completion(st.session_state.health_profile)
    st.metric("Profile completeness", f"{completion}%")
    st.progress(completion / 100)
    st.info("This tool gives general advice, not medical guidance.")
    if st.button("Reset to example profile"):
        st.session_state.health_profile = DEFAULT_PROFILE.copy()
        st.success("Profile reset to example values.")


tab1, tab2, tab3 = st.tabs(["Meal Planning", "Food Analysis", "Health Insights"])

with tab1:
    st.subheader("Personalized Meal Planning")
    col1, col2 = st.columns([2, 1])

    with col1:
        user_input = st.text_area(
            "Describe any extra needs for your meal plan",
            placeholder="Example: Quick meals for busy weekdays",
        )
        plan_days = st.selectbox("Plan length", [3, 5, 7], index=2)
        meal_focus = st.selectbox(
            "Main focus", ["Balanced", "Weight loss", "Muscle gain", "More energy"]
        )
        include_snacks = st.checkbox("Include snacks", value=True)

    with col2:
        st.markdown("### Profile Snapshot")
        with st.expander("View profile details", expanded=False):
            st.json(st.session_state.health_profile)
        st.caption("Update the profile in the sidebar if needed.")

    if st.button("Generate Personalized Meal Plan", key="meal_plan_btn"):
        if not any(st.session_state.health_profile.values()):
            st.warning("Please complete your health profile in the sidebar first.")
        else:
            with st.spinner("Creating your meal plan..."):
                prompt_lines = [
                    "Create a personalized meal plan based on the following profile.",
                    f"Health goals: {st.session_state.health_profile['goals']}",
                    f"Medical conditions: {st.session_state.health_profile['conditions']}",
                    f"Fitness routines: {st.session_state.health_profile['routines']}",
                    f"Food preferences: {st.session_state.health_profile['preferences']}",
                    f"Dietary restrictions: {st.session_state.health_profile['restrictions']}",
                    f"Plan length: {plan_days} days",
                    f"Main focus: {meal_focus}",
                    f"Include snacks: {'Yes' if include_snacks else 'No'}",
                    f"Additional requirements: {user_input if user_input else 'None'}",
                    "Provide:",
                    "1) A day-by-day plan with breakfast, lunch, dinner"
                    + (" and snacks." if include_snacks else "."),
                    "2) A simple nutritional breakdown for each day (calories, macros).",
                    "3) Short reasons for the meal choices.",
                    "4) A shopping list organized by category.",
                    "5) Prep tips and time-saving ideas.",
                    "Use clear headings and bullet points. Keep language simple.",
                ]
                prompt = "\n".join(prompt_lines)
                response = get_gemini_response(prompt)
                if response:
                    st.session_state.meal_plan_text = response

            show_response(
                "Your Personalized Meal Plan",
                st.session_state.get("meal_plan_text", ""),
            )

            if st.session_state.get("meal_plan_text"):
                st.download_button(
                    label="Download Meal Plan",
                    data=st.session_state.meal_plan_text,
                    file_name="personalized_meal_plan.txt",
                    mime="text/plain",
                )

with tab2:
    st.subheader("Food Analysis")
    st.caption("For best results, upload a clear photo with good lighting.")
    uploaded_file = st.file_uploader("Upload an image of your food", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded food image", use_column_width=True)

    if st.button("Analyze Food", key="food_analysis"):
        if uploaded_file is None:
            st.warning("Please upload an image to analyze.")
        else:
            with st.spinner("Analyzing your food..."):
                image_data = input_image_setup(uploaded_file)
                prompt = (
                    "You are a nutrition assistant. Analyze this food image.\n"
                    "Provide:\n"
                    "- Estimated calories\n"
                    "- Macronutrient breakdown\n"
                    "- Potential health benefits\n"
                    "- Common dietary concerns\n"
                    "- Suggested portion size\n"
                    "If there are multiple items, analyze each separately."
                )
                response = get_gemini_response(prompt, image_data)
                show_response("Food Analysis Results", response)

with tab3:
    st.subheader("Health Insights")
    health_query = st.text_input(
        "Ask a health or nutrition question",
        placeholder="Example: How can I improve gut health?",
    )
    detail_level = st.selectbox("Answer depth", ["Short and simple", "Detailed"])

    if st.button("Get Expert Insights", key="health_insights"):
        if not health_query:
            st.warning("Please enter a health question.")
        else:
            with st.spinner("Researching your question..."):
                prompt = (
                    "You are a certified nutritionist and health expert.\n"
                    f"Question: {health_query}\n"
                    f"Answer depth: {detail_level}\n"
                    f"User profile: {st.session_state.health_profile}\n"
                    "Include:\n"
                    "1) A clear explanation in simple language.\n"
                    "2) Practical recommendations.\n"
                    "3) Any relevant precautions.\n"
                    "4) Suggested foods or supplements if appropriate.\n"
                    "Use headings and bullet points."
                )
                response = get_gemini_response(prompt)
                show_response("Expert Health Insights", response)
