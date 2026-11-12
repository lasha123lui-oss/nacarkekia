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
