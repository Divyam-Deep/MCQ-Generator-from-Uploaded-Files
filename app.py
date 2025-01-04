import os
import streamlit as st
import pdfplumber
import docx
from fpdf import FPDF
import google.generativeai as genai
from werkzeug.utils import secure_filename

# Set up API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAcGSzh6iChS-jN3voTzowXPNyMYqw4f1Q"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-pro")

# Define allowed extensions and directories
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
UPLOAD_FOLDER = 'uploads/'
RESULTS_FOLDER = 'results/'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        with pdfplumber.open(file_path) as pdf:
            text = ''.join([page.extract_text() for page in pdf.pages])
        return text
    elif ext == 'docx':
        doc = docx.Document(file_path)
        text = ' '.join([para.text for para in doc.paragraphs])
        return text
    elif ext == 'txt':
        with open(file_path, 'r') as file:
            return file.read()
    return None

def Question_mcqs_generator(input_text, num_questions):
    prompt = f"""
    You are an AI assistant helping the user generate multiple-choice questions (MCQs) based on the following text:
    '{input_text}'
    Please generate {num_questions} MCQs from the text. Each question should have:
    - A clear question
    - Four answer options (labeled A, B, C, D)
    - The correct answer clearly indicated
    Format:
    ## MCQ
    Question: [question]
    A) [option A]
    B) [option B]
    C) [option C]
    D) [option D]
    Correct Answer: [correct option]
    """
    response = model.generate_content(prompt).text.strip()
    return response

def save_mcqs_to_file(mcqs, filename):
    results_path = os.path.join(RESULTS_FOLDER, filename)
    with open(results_path, 'w') as f:
        f.write(mcqs)
    return results_path

def create_pdf(mcqs, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for mcq in mcqs.split("## MCQ"):
        if mcq.strip():
            pdf.multi_cell(0, 10, mcq.strip())
            pdf.ln(5)  # Add a line break

    pdf_path = os.path.join(RESULTS_FOLDER, filename)
    pdf.output(pdf_path)
    return pdf_path

# Streamlit App with enhanced UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Pacifico&display=swap');

    .stApp {
        background-image: url("https://i.pinimg.com/736x/52/c2/83/52c28398cc986190e1221b9efa250379.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        font-family: 'Roboto', sans-serif;
    }
    .title {
        text-align: center;
        font-size: 2.5em;
        font-family: 'Roboto Slab', cursive;
        color: white;
        margin-bottom: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #f7f9fc;
    }
    .stButton>button {
        background-color: transparent;
        color: white;
        border: 2px solid red;
        border-radius: 5px;
        font-size: 16px;
        padding: 10px 20px;
        margin-top: 10px;
        font-family: 'Roboto', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='title'>MCQ Generator from Uploaded Files</div>", unsafe_allow_html=True)

# File Upload
uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    filename = secure_filename(uploaded_file.name)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.read())

    # Extract text
    text = extract_text_from_file(file_path)
    if text:
        st.success("File uploaded and text extracted successfully!")
        st.text_area("Extracted Text Preview", text[:500], height=200)

        # Number of questions
        num_questions = st.number_input("Number of MCQs to generate", min_value=1, max_value=50, value=5, step=1)

        if st.button("Generate MCQs"):
            try:
                mcqs = Question_mcqs_generator(text, num_questions)
                st.subheader("Generated MCQs")
                st.text_area("MCQs", mcqs, height=400)

                # Save MCQs
                txt_filename = f"generated_mcqs_{filename.rsplit('.', 1)[0]}.txt"
                pdf_filename = f"generated_mcqs_{filename.rsplit('.', 1)[0]}.pdf"
                txt_path = save_mcqs_to_file(mcqs, txt_filename)
                pdf_path = create_pdf(mcqs, pdf_filename)

                st.download_button("Download MCQs as Text File", open(txt_path, 'rb'), txt_filename)
                st.download_button("Download MCQs as PDF", open(pdf_path, 'rb'), pdf_filename)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.error("Unable to extract text from the uploaded file.")

