# ✅ Fully Integrated Enhanced Fitness Assistant App

import streamlit as st
import json
import os
import requests
from fpdf import FPDF
import fitz  # PyMuPDF
import plotly.graph_objects as go
import plotly.io as pio
import time
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# -------- CONFIG --------
# Load Groq API key from Streamlit secrets
#if "GROQ_API_KEY" in st.secrets:
#    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
#else:
#    st.error("Missing GROQ_API_KEY in .streamlit/secrets.toml")
#    st.stop()

GROQ_API_KEY = "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"

GROQ_MODEL = "llama3-70b-8192"
DATA_FILE = "user_data.json"
RESPONSES_FILE = "agent_responses.json"

# Initialize session state
st.session_state.setdefault("latest_plan", "")
st.session_state.setdefault("theme_mode", "light")
st.session_state.setdefault("agent_responses", {})

# -------- UTILS --------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"personal": {}, "goals": [], "nutrition": {}, "notes": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

template = """You are an AI language model assistant. Your task is to generate five
different versions of the given user question. By generating multiple perspectives on the user question, your goal is to help
the user overcome some of the limitations of the distance-based similarity search.
Provide these alternative questions separated by newlines. Original question: {question}"""
prompt_perspectives = ChatPromptTemplate.from_template(template)

def call_groq(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {"messages": [{"role": "user", "content": prompt}], "model": GROQ_MODEL}
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
    if res.status_code != 200:
        st.error(f"Groq API Error: {res.status_code} - {res.text}")
        return "❌ Groq API error."
    try:
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error parsing Groq response: {e}")
        return "❌ Failed to parse Groq response."

def update_feedback(orig_prompt, feedback_label):
    # Create a unique form key
    form_key = "nutrition_feedback_form"
    
    # Create a form for the feedback
    with st.form(key=form_key):
        # Text area for feedback inside the form
        feedback_text = st.text_area(
            label=feedback_label,
            max_chars=500,
            height=150,
            key="feedback_textarea"
        )
        
        # Submit button inside the form
        submit_pressed = st.form_submit_button(label="Update My Plan")
    
    # Handle form submission
    if submit_pressed and feedback_text:
        with st.spinner("Updating your nutrition plan..."):
            # Get current user data directly from the data object
            current_data = load_data()
            current_age = current_data["personal"].get("age", 30)
            current_gender = current_data["personal"].get("gender", "Male")
            current_weight = current_data["personal"].get("weight", 70)
            current_goals = current_data.get("goals", ["Fitness"])
            
            # Create a very clear and direct prompt
            modification_prompt = f"""
            As a nutrition expert, create a NEW MEAL PLAN with these specifications:
            
            USER PROFILE:
            - Age: {current_age} years old
            - Gender: {current_gender}
            - Weight: {current_weight}kg
            - Goals: {', '.join(current_goals)}
            
            USER REQUEST:
            "{feedback_text}"
            
            The user's request above is VERY IMPORTANT and must be followed precisely.
            Create a detailed meal plan that implements these exact requirements.
            """
            
            st.write("Processing your request...")
            
            # Make direct API call to ensure it works
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "messages": [{"role": "user", "content": modification_prompt}],
                    "model": GROQ_MODEL,
                    "temperature": 0.5  # Lower temperature for more focused responses
                }
                
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=body
                )
                
                if response.status_code == 200:
                    result = response.json()
                    new_plan = result["choices"][0]["message"]["content"]
                    
                    # Store the updated plan
                    st.session_state["nutrition_plan"] = new_plan
                    current_data["nutrition_plan"] = new_plan
                    save_data(current_data)
                    
                    # Display the new plan
                    st.success("Your nutrition plan has been updated successfully!")
                    
                    # Show the updated plan directly
                    st.subheader("Your Updated Nutrition Plan:")
                    st.info(new_plan)
                    
                    # This will ensure page elements are updated
                    st.experimental_rerun()
                else:
                    error_details = response.json() if response.content else {"error": "No details available"}
                    st.error(f"Error from API: {response.status_code} - {error_details}")
                    
            except Exception as e:
                st.error(f"Error updating your nutrition plan: {str(e)}")
                st.write("Please try again or contact support if the problem persists.")
    elif submit_pressed and not feedback_text:
        st.warning("Please enter your dietary preferences or requirements before submitting.")
    
    # Add a separator to clearly distinguish this section
    st.markdown("---")
    return

def export_pdf_from_text(title, text_dict):
    try:
        # Create PDF with wider margins and strict text handling
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        
        # Set generous margins
        pdf.set_margins(left=20, top=20, right=20)
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # Add first page
        pdf.add_page()
        
        # Use built-in fonts only
        pdf.set_font("Helvetica", "B", 14)
        
        # Add title
        pdf.cell(w=0, h=10, txt=title, border=0, ln=1, align="C")
        pdf.ln(5)
        
        # Process each section with careful text handling
        for key, val in text_dict.items():
            # Section headers with smaller font
            pdf.set_font("Helvetica", "B", 12)
            
            # Ensure header text is clean and limited in length
            header_text = str(key)[:40]  # Limit header length
            pdf.cell(0, 8, header_text, 0, 1)
            
            # Normal text for content
            pdf.set_font("Helvetica", "", 10)
            
            # Handle content by breaking into small, manageable pieces
            content = str(val) if val is not None else ""
            
            # Process each paragraph safely
            for paragraph in content.split("\n"):
                if paragraph.strip():  # Skip empty paragraphs
                    # Process paragraph in very small chunks
                    for i in range(0, len(paragraph), 80):
                        # Take a chunk of text and clean it
                        chunk = paragraph[i:i+80]
                        
                        # Clean the text - remove problematic characters
                        clean_chunk = "".join(c if ord(c) < 128 else '?' for c in chunk)
                        
                        try:
                            # Use write instead of multi_cell for more reliable rendering
                            pdf.write(5, clean_chunk)
                            
                            # If this is not the last chunk, don't add line break
                            if i + 80 < len(paragraph):
                                pdf.write(5, " ")
                            else:
                                pdf.ln()
                        except Exception:
                            # If a specific chunk causes problems, skip it
                            pdf.write(5, "[...]")
                            pdf.ln()
            
            # Add space between sections
            pdf.ln(5)
        
        # Generate PDF as bytes
        return pdf.output(dest="S").encode('latin-1', 'replace')
    except Exception as e:
        # If PDF generation fails, provide a simple text file instead
        st.error(f"PDF generation failed: {e}")
        
        # Create a simple text file as fallback
        text_content = title + "\n\n"
        for k, v in text_dict.items():
            text_content += f"--- {k} ---\n{v}\n\n"
        
        return text_content.encode('utf-8')

def extract_pdf_text(uploaded):
    with fitz.open(stream=uploaded.read(), filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)

# -------- PAGE CONFIG --------
st.set_page_config(page_title="AI Fitness Assistant", layout="wide")

# -------- SIDEBAR --------
st.sidebar.title("⚙️ Settings")
if st.sidebar.button("🔄 Reset All Data"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    if os.path.exists(RESPONSES_FILE): os.remove(RESPONSES_FILE)
    for k in ["latest_plan","agent_responses"]:
        st.session_state.pop(k, None)
    st.success("Data reset. Please refresh the page.")
    st.stop()

mode = st.sidebar.selectbox("Theme", ["Light","Dark"],
                            index=0 if st.session_state.theme_mode=="light" else 1)
st.session_state.theme_mode = mode.lower()
if st.session_state.theme_mode == "dark":
    st.markdown("""
        <style>
            body, .stApp { background-color: #0e1117; color: white; }
            .stTextInput input, .stTextArea textarea, .stNumberInput input { background: #1a1a1a; color: white; }
            .stButton button { background: #333; color: white; border: 1px solid #888; }
        </style>
    """, unsafe_allow_html=True)
    pio.templates.default = "plotly_dark"
else:
    pio.templates.default = "plotly"
    st.markdown("""
    <style>
        body, .stApp {
            background-color: #f9f9f9;
            color: #333333;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        .css-1d391kg, .css-12w0qpk {
            background-color: #ffffff !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
        .stButton>button {
            background-color: #007bff !important;
            color: white !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 0.5rem 1rem !important;
        }
        .stButton>button:hover {
            background-color: #0069d9 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# -------- LOAD DATA --------
data = load_data()

# -------- HEADER --------
st.title("🏋️ AI Fitness Assistant")
st.write("Groq-powered • Personalized • Interactive")

# -------- PERSONAL INFO --------
st.markdown("---")
st.subheader("👤 Personal Information")
with st.form("profile_form"):
    name   = st.text_input("Name",  data["personal"].get("name",""))
    age    = st.number_input("Age",  min_value=0,  max_value=120, value=data["personal"].get("age",0))
    weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, value=data["personal"].get("weight",0.0))
    height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=data["personal"].get("height",0.0))
    gender = st.selectbox("Gender", ["Male","Female","Other"], index=0)
    if st.form_submit_button("Save Profile"):
        data["personal"] = {"name":name,"age":age,"weight":weight,"height":height,"gender":gender}
        save_data(data); st.success("Profile saved!")

# -------- GOALS --------
st.markdown("---")
st.subheader("🎯 Fitness Goals")
goals = st.multiselect("Goals", ["Muscle Gain","Weight Loss","Endurance","Rehab"], data.get("goals",[]))
if st.button("Save Goals"):
    data["goals"] = goals; save_data(data); st.success("Goals saved!")

# -------- NUTRITION --------

st.markdown("---")
st.subheader("🍎 Nutrition Targets")
calories = st.number_input("Calories", value=data.get("nutrition",{}).get("calories",2000))
protein  = st.number_input("Protein (g)", value=data.get("nutrition",{}).get("protein",100))
fat      = st.number_input("Fat (g)", value=data.get("nutrition",{}).get("fat",70))
carbs    = st.number_input("Carbs (g)", value=data.get("nutrition",{}).get("carbs",250))

# Initialize nutrition_plan in session state if it doesn't exist
if "nutrition_plan" not in st.session_state:
    st.session_state.nutrition_plan = data.get("nutrition_plan", "")

col1,col2= st.columns(2)
with col1:
    if st.button("Save Nutrition"):
        data["nutrition"] = {"calories":calories,"protein":protein,"fat":fat,"carbs":carbs}
        # Preserve the nutrition plan when saving nutrition data
        if "nutrition_plan" in st.session_state and st.session_state.nutrition_plan:
            data["nutrition_plan"] = st.session_state.nutrition_plan
        save_data(data)
        st.success("Nutrition saved!")
with col2:
    if st.button("AI Nutrition Plan"):
        prompt = f"Generate meal plan for a {age}-year-old {gender} {weight}kg aiming {', '.join(goals)}."
        print(prompt)
        plan = call_groq(prompt)
        # Store the plan in session state and data
        st.session_state.nutrition_plan = plan
        data["nutrition_plan"] = plan
        save_data(data)
        st.info(plan)
        feedback_label = "If you would like to make any changes to your nutritional plan, please enter below"
        update_feedback(prompt, feedback_label)

# Display the saved nutrition plan if it exists
if st.session_state.nutrition_plan:
    st.markdown("### Your Nutrition Plan:")
    st.info(st.session_state.nutrition_plan)

# -------- MACRO CHART --------
if data.get("nutrition"):
    st.markdown("---")
    st.subheader("📊 Macro Breakdown")
    m = data["nutrition"]
    fig = go.Figure(go.Bar(
        x=[m["protein"],m["fat"],m["carbs"]],
        y=["Protein","Fat","Carbs"],
        orientation='h'
    ))
    fig.update_layout(template=pio.templates.default, height=300)
    st.plotly_chart(fig, use_container_width=True)

# -------- NOTES --------
st.markdown("---")
st.subheader("📝 Special Notes")
for i,note in enumerate(data["notes"]):
    cols = st.columns([4,1,1])
    new_note = cols[0].text_input("", note, key=f"note_{i}")
    if cols[1].button("💾 Save", key=f"save_{i}"):
        data["notes"][i] = new_note
        save_data(data)
        st.success(f"Note saved!")
        # Use JavaScript to refresh the page instead of st.rerun()
        st.markdown(
            """
            <script>
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            </script>
            """, 
            unsafe_allow_html=True
        )
    if cols[2].button("❌ Delete", key=f"del_{i}"):
        data["notes"].pop(i)
        save_data(data)
        st.success(f"Note deleted!")
        # Use JavaScript to refresh the page instead of st.rerun()
        st.markdown(
            """
            <script>
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            </script>
            """, 
            unsafe_allow_html=True
        )
new_note = st.text_input("Add a new note")
if st.button("Add Note") and new_note:
    data["notes"].append(new_note)
    save_data(data)
    st.success("Note added!")
    # Use JavaScript to refresh the page instead of st.rerun()
    st.markdown(
        """
        <script>
            setTimeout(function() {
                window.location.reload();
            }, 1500);
        </script>
        """, 
        unsafe_allow_html=True
    )

# -------- PDF UPLOAD --------
st.markdown("---")
st.subheader("📤 Upload Workout Plan (PDF)")
uploaded_file = st.file_uploader("Drop your PDF here", type="pdf")
if uploaded_file:
    pdf_text = extract_pdf_text(uploaded_file)
    st.text_area("Extracted Text", pdf_text, height=200)

# -------- MULTI-AGENT --------
st.markdown("---")
st.subheader("🧠 Multi-Agent Assistant")
tabs = st.tabs(["🏋️ Workout Planner","🥗 Nutritionist","🦵 Rehab Advisor","🧮 Fitness Calculator"])

with tabs[0]:
    query = st.text_input("👟 Workout Question", key="mq1")
    if st.button("Ask Workout Planner", key="b1") and query.strip():
        with st.spinner("Planning your workout..."):
            prompt = (
                f"Design a personalized workout plan for the following user:\n"
                f"Profile: {data['personal']}\n"
                f"Goals: {', '.join(goals)}\n"
                f"Notes: {'; '.join(data['notes'])}\n"
                f"Question: {query}"
            )
            response = call_groq(prompt)
            st.session_state.agent_responses['Workout Planner'] = response
            st.markdown("#### 💡 Response:")
            st.success(response)

with tabs[1]:
    query = st.text_input("🥗 Nutrition Question", key="mq2")
    if st.button("Ask Nutritionist", key="b2") and query.strip():
        with st.spinner("Consulting nutritionist..."):
            prompt = (
                f"You are a certified fitness nutritionist.\n"
                f"Profile: {data['personal']}\nGoals: {', '.join(goals)}\nNotes: {'; '.join(data['notes'])}\n"
                f"Question: {query}"
            )
            response = call_groq(prompt)
            st.session_state.agent_responses['Nutritionist'] = response
            st.markdown("#### 💡 Response:")
            st.info(response)

with tabs[2]:
    query = st.text_input("🦵 Rehab Question", key="mq3")
    if st.button("Ask Rehab Advisor", key="b3") and query.strip():
        with st.spinner("Consulting rehab advisor..."):
            prompt = (
                f"You are a certified rehab specialist.\n"
                f"Profile: {data['personal']}\nInjury Notes: {'; '.join(data['notes'])}\n"
                f"Question: {query}"
            )
            response = call_groq(prompt)
            st.session_state.agent_responses['Rehab Advisor'] = response
            st.markdown("#### ⚠️ Caution:")
            st.warning(response)

with tabs[3]:
    query = st.text_input("🧮 Calculation Question", key="mq4")
    if st.button("Ask Fitness Calculator", key="b4") and query.strip():
        with st.spinner("Crunching numbers..."):
            prompt = f"You are a fitness calculator assistant. Question: {query}"
            response = call_groq(prompt)
            st.session_state.agent_responses['Fitness Calculator'] = response
            st.markdown("#### 🧮 Result:")
            st.success(response)

# -------- DOWNLOAD RESPONSES --------
st.markdown("---")
st.subheader("📄 Download All Agent Responses")
if st.session_state.agent_responses:
    pdf_bytes = export_pdf_from_text("AI Fitness Assistant Responses", st.session_state.agent_responses)
    st.download_button("📥 Download Responses as PDF", data=pdf_bytes, file_name="fitness_agent_responses.pdf", mime="application/pdf")
