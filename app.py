
import streamlit as st
import requests

st.set_page_config(
    page_title="ნაცარქექია",
    page_icon="🧠"
)

st.title("🧠 ნაცარქექია")
st.write("გამარჯობა! მე ვარ ნაცარქექია.")
st.write("შენი პირადი საძიებო ასისტენტი.")

question = st.text_input("მკითხე რამე:")

if st.button("მოძებნე") and question:
    api_key = st.secrets.get("SERPAPI_API_KEY", "")

    if not api_key:
        st.error("SerpApi გასაღები ვერ მოიძებნა. შეამოწმე Streamlit Secrets.")
    else:
        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google",
                    "q": question,
                    "api_key": api_key,
                    "hl": "ka",
                    "gl": "ge"
                },
                timeout=20
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("organic_results", [])

            if results:
                st.subheader("ძიების შედეგები")
                for item in results[:5]:
                    st.markdown(f"### {item.get('title', 'უსათაურო')}")
                    st.write(item.get("snippet", ""))
                    if item.get("link"):
                        st.markdown(f"[წყაროს ნახვა]({item['link']})")
            else:
                st.info("შედეგები ვერ მოიძებნა.")

        except Exception as e:
            st.error(f"ძიების შეცდომა: {e}")

