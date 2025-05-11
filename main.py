import streamlit as st
from datetime import datetime, date
import json
import os

# Medicine Reminder Class
class MedicineReminder:
    def __init__(self, name, dosage, reminder_time, weekdays, quantity, taken_log=None):
        self.name = name
        self.dosage = dosage
        self.reminder_time = reminder_time
        self.weekdays = weekdays
        self.quantity = quantity 
        self.taken_log = taken_log or {}

    def to_dict(self):
        return {
            "name": self.name,
            "dosage": self.dosage,
            "reminder_time": self.reminder_time,
            "weekdays": self.weekdays,
            "quantity": self.quantity,
            "taken_log": self.taken_log
        }

    @staticmethod
    def from_dict(data):
        return MedicineReminder(
            name=data.get("name", ""),
            dosage=data.get("dosage", ""),
            reminder_time=data.get("reminder_time", ""),
            weekdays=data.get("weekdays", []),
            quantity=data.get("quantity", 0),
            taken_log=data.get("taken_log", {})
        )

# Reminder Manager Class
class ReminderManager:
    def __init__(self, file_path="reminders.json"):
        self.file_path = file_path
        self.reminders = self.load_reminders()

    def load_reminders(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r") as f:
            try:
                data = json.load(f)
                return [MedicineReminder.from_dict(item) for item in data]
            except json.JSONDecodeError:
                return []

    def save_reminders(self):
        with open(self.file_path, "w") as f:
            json.dump([r.to_dict() for r in self.reminders], f, indent=4)

    def add_reminder(self, name, dosage, reminder_time, weekdays, quantity):
        reminder = MedicineReminder(name, dosage, reminder_time, weekdays, quantity)
        self.reminders.append(reminder)
        self.save_reminders()

    def delete_reminder(self, index):
        if 0 <= index < len(self.reminders):
            del self.reminders[index]
            self.save_reminders()

    def mark_taken(self, index):
        today_str = str(date.today())
        self.reminders[index].taken_log[today_str] = True
        if self.reminders[index].quantity > 0:
            self.reminders[index].quantity -= 1
        self.save_reminders()

    def mark_untaken(self, index):
        today_str = str(date.today())
        self.reminders[index].taken_log[today_str] = False
        self.save_reminders()

    def get_due_reminders(self, current_time):
        current_str = current_time.strftime("%I:%M %p")
        today_day = current_time.strftime("%A")
        due = []
        for i, r in enumerate(self.reminders):
            if r.reminder_time == current_str and today_day in r.weekdays:
                due.append((i, r))
        return due

    def get_all_reminders(self):
        return sorted(self.reminders, key=lambda x: x.reminder_time)

# Streamlit App
st.set_page_config("💊 Medicine Reminder Buddy", layout="centered")
st.markdown("<h1 style='text-align: center; color: teal;'>💊 Medicine Reminder Buddy</h1>", unsafe_allow_html=True)

if "manager" not in st.session_state:
    st.session_state.manager = ReminderManager()

st.markdown("### ➕ Add a New Reminder")
with st.form("reminder_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Medicine Name")
        quantity = st.number_input("Tablet Quantity", min_value=1, step=1)
    with col2:
        dosage = st.text_input("Dosage (e.g., per day)")
        reminder_time = st.time_input("Reminder Time")

    weekdays = st.multiselect(
        "Repeat on Days",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=[]
    )

    submit = st.form_submit_button("Add Reminder")

    if submit:
        formatted_time = reminder_time.strftime("%I:%M %p")
        st.session_state.manager.add_reminder(name, dosage, formatted_time, weekdays, quantity)
        st.success("✅ Reminder added successfully!")

# Display Reminders
st.markdown("### 📋 Your Reminders")
reminders = st.session_state.manager.get_all_reminders()

if reminders:
    for i, reminder in enumerate(reminders):
        taken_today = reminder.taken_log.get(str(date.today()), False)
        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 10px; margin-bottom: 10px; ">
                <strong>🧾 {reminder.name}</strong><br>
                Dosage: {reminder.dosage} | Time: <span style="color: green;">{reminder.reminder_time}</span><br>
                Days: {', '.join(reminder.weekdays)} | Quantity Left: <b>{reminder.quantity}</b><br>
                Status Today: {"✅ Taken" if taken_today else "❌ Not Taken"}
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🗑 Delete", key=f"delete_{i}_{reminder.name}"):
                    st.session_state.manager.delete_reminder(i)
                    st.rerun()
            with col2:
                if st.button("✅ Mark Taken", key=f"taken_{i}_{reminder.name}"):
                    st.session_state.manager.mark_taken(i)
                    st.success(f"Marked {reminder.name} as taken.")
                    st.rerun()
            with col3:
                if st.button("❌ Mark Not Taken", key=f"untaken_{i}_{reminder.name}"):
                    st.session_state.manager.mark_untaken(i)
                    st.warning(f"Marked {reminder.name} as not taken.")
                    st.rerun()
else:
    st.info("No reminders yet. Add one above!")

# Check Due
if st.button("⏰ Check for Due Reminders"):
    now = datetime.now()
    due_reminders = st.session_state.manager.get_due_reminders(now)
    if due_reminders:
        for index, reminder in due_reminders:
            st.toast(f"💊 Reminder: Take {reminder.quantity} tablets of {reminder.name} {reminder.dosage} times in a day!", icon="⏰")
            if st.button(f"✅ I have taken {reminder.name}", key=f"confirm_{index}_{reminder.name}"):
                st.session_state.manager.mark_taken(index)
                st.success(f"You have taken {reminder.name}. Good job!")
                st.rerun()
    else:
        st.success("✅ No medicines due at this moment.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center;'> Made by Ayesha Nasir ❤️ </p>", unsafe_allow_html=True)
