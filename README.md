# AI Fitness Assistant

This repository contains a **Streamlit-based AI Fitness Assistant** powered by Groq's Llama 3 model. The app provides:

- **User Profile Management**: Collect and save personal data (name, age, weight, height, gender).
- **Goal Tracking**: Select fitness goals (muscle gain, weight loss, endurance, rehab).
- **Nutrition Planning**: Set macronutrient targets and generate meal plans via AI.
- **Interactive Macro Chart**: Visualize protein, fat, and carb breakdown with Plotly.
- **Special Notes**: Log and edit notes such as injuries or limitations.
- **Multi-Agent AI**: Dedicated tabs for Workout Planner, Nutritionist, Rehab Advisor, and Fitness Calculator with context-aware prompts and loading spinners.
- **PDF Handling**:
  - Upload existing workout plan PDFs and extract text.
  - Export AI-generated responses as professional PDF reports.
- **Theme Toggle & Reset**: Switch between light/dark modes and reset all data.

## Setup & Installation

1. **Clone this repository**:

   ```bash
   git clone https://github.com/<your-username>/fitness-assistant.git
   cd fitness-assistant
   ```

2. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set your Groq API key**:

   Open `main.py` and replace `your_groq_api_key_here` with your actual API key:

   ```python
   GROQ_API_KEY = "gsk_..."
   ```

5. **Run the app**:

   ```bash
   streamlit run main.py
   ```

## Usage

- Navigate through sidebar to **reset data** or switch **theme**.
- Fill in personal info, goals, nutrition targets, and notes on the main page.
- Use the **Multi-Agent** tabs to get specialized AI assistance.
- Download reports or upload PDFs to interact with existing plans.

## License

This project is open source under the MIT License. Feel free to contribute!

