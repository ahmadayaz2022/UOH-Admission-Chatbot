# ✅ University of Haripur Admission Chatbot (with Send Button)
# Install dependencies
!pip install requests beautifulsoup4 groq gradio schedule --quiet

import requests
from bs4 import BeautifulSoup
import gradio as gr
import schedule
import threading
import time
from groq import Groq
import os

# ==== SETUP ====
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # Secure from Hugging Face Secrets
client = Groq(api_key=GROQ_API_KEY)
chat_history = []
UOH_DATA = {}

# ==== Scraper ====
def update_uoh_data():
    global UOH_DATA
    UOH_DATA = {}

    try:
        r = requests.get("https://www.uoh.edu.pk/admissions/schedule")
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find(string="Activity").find_parent("table")
        rows = table.find_all("tr")
        schedule_info = {}
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) == 2:
                schedule_info[cols[0].get_text(strip=True)] = cols[1].get_text(strip=True)
        UOH_DATA['admission_schedule'] = schedule_info
    except: pass

    try:
        r2 = requests.get("https://www.uoh.edu.pk/admissions/bs-programs")
        soup2 = BeautifulSoup(r2.text, "html.parser")
        bs = [li.get_text(strip=True).split(" (")[0] for li in soup2.find_all("li")]
        UOH_DATA['bs_programs'] = bs
    except: pass

    try:
        r3 = requests.get("https://www.uoh.edu.pk/admissions/graduate-programs")
        soup3 = BeautifulSoup(r3.text, "html.parser")
        ms_phd = [li.get_text(strip=True) for li in soup3.find_all("li")]
        UOH_DATA['ms_phd_programs'] = ms_phd
    except: pass

    try:
        r4 = requests.get("https://www.uoh.edu.pk/admissions/eligibility")
        soup4 = BeautifulSoup(r4.text, "html.parser")
        cr = soup4.find_all("tr")
        eligibility = {}
        for tr in cr[1:]:
            cols = tr.find_all("td")
            if len(cols) >= 3:
                program = cols[1].get_text(strip=True)
                criteria = cols[2].get_text(strip=True)
                eligibility[program] = criteria
        UOH_DATA['eligibility'] = eligibility
    except: pass

    try:
        r5 = requests.get("https://www.uoh.edu.pk/admissions/entry-test")
        soup5 = BeautifulSoup(r5.text, "html.parser")
        text = soup5.get_text(strip=True)
        UOH_DATA['entry_test'] = text if text else "Entry test info not available."
    except: pass

    try:
        r6 = requests.get("https://www.uoh.edu.pk/fee-structure")
        soup6 = BeautifulSoup(r6.text, "html.parser")
        text = soup6.get_text(separator="\n", strip=True)
        UOH_DATA['fee_structure'] = text[:1000] + "..."
    except: pass

    try:
        r7 = requests.get("https://www.uoh.edu.pk/facilities/hostel")
        soup7 = BeautifulSoup(r7.text, "html.parser")
        text = soup7.get_text(separator="\n", strip=True)
        UOH_DATA['hostel'] = text[:800] + "..."
    except: pass

    try:
        r8 = requests.get("https://www.uoh.edu.pk/students/scholarships")
        soup8 = BeautifulSoup(r8.text, "html.parser")
        text = soup8.get_text(separator="\n", strip=True)
        UOH_DATA['scholarships'] = text[:800] + "..."
    except: pass

update_uoh_data()
schedule.every(6).hours.do(update_uoh_data)
threading.Thread(target=lambda: [schedule.run_pending() or time.sleep(60)], daemon=True).start()

# ==== Prompt ====
def build_prompt():
    sched = "\n".join([f"- {k}: {v}" for k,v in UOH_DATA.get('admission_schedule', {}).items()])
    bs = ", ".join(UOH_DATA.get('bs_programs', [])[:5]) + ", ..."
    ms = ", ".join(UOH_DATA.get('ms_phd_programs', [])[:5]) + ", ..."
    fee = UOH_DATA.get('fee_structure', 'Not available')
    hostel = UOH_DATA.get('hostel', 'Not available')
    scholarships = UOH_DATA.get('scholarships', 'Not available')
    return f"""
You are a helpful assistant for the University of Haripur (UoH), Pakistan.
Admission Schedule:
{sched}
BS Programs: {bs}
MS/PhD Programs: {ms}
Entry Test Info: {UOH_DATA.get('entry_test', 'Not available.')}
Fee Structure: {fee}
Hostel Info: {hostel}
Scholarship Info: {scholarships}
Be polite and explain everything step-by-step.
"""

# ==== Chat Logic ====
def uoh_chatbot(user_input):
    chat_history.append({"role": "user", "content": user_input})
    prompt = build_prompt()
    messages = [{"role": "system", "content": prompt}] + chat_history
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"❌ Error: {e}"
    chat_history.append({"role": "assistant", "content": reply})
    return reply

# ==== Gradio UI ====
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🎓 University of Haripur Admission Chatbot")
    chatbot = gr.Chatbot(height=400)
    with gr.Row():
        msg = gr.Textbox(placeholder="Ask anything about UOH...", show_label=False, scale=9)
        send = gr.Button("➡️", scale=1)
    clr = gr.Button("🧹 Clear Chat")

    def respond(m, h):
        r = uoh_chatbot(m)
        h.append((m, r))
        return h, ""

    msg.submit(respond, [msg, chatbot], [chatbot, msg])
    send.click(respond, [msg, chatbot], [chatbot, msg])
    clr.click(lambda: ([], ""), None, [chatbot, msg])

demo.launch()