lasha123lui-oss
nacarkekia
Repository navigation
Code
Issues
Pull requests
Agents
Actions
nacarkekia
/
app.py
in
main

Edit

Preview
Indent mode

Spaces
Indent size

4
Line wrap mode

No wrap
Editing app.py file contents
  1
  2
  3
  4
  5
  6
  7
  8
  9
 10
 11
 12
 13
 14
 15
 16
 17
import streamlit as st

st.set_page_config(
    page_title="ნაცარქექია",
    page_icon="🧠"
)

st.title("🧠 ნაცარქექია")
st.write("გამარჯობა! მე ვარ ნაცარქექია.")
st.write("შენი პირადი AI ასისტენტი, რომელიც თანდათან ისწავლის შენს საუბრის სტილს.")

question = st.text_input("მკითხე რამე:")

if question:
    st.write("შენი კითხვა:", question)
    st.info("ჯერ სწავლის პროცესში ვარ. მალე პასუხის გაცემასაც შევძლებ!")

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
