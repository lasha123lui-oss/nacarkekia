
import streamlit as st
import requests

st.set_page_config(page_title="ნაცარქექია", page_icon="🧠")

st.title("🧠 ნაცარქექია")
st.write("შენი პირადი ქართული AI ასისტენტი.")

question = st.text_input("მკითხე რამე:")

use_search = st.checkbox(
    "ინტერნეტშიც მოძებნე პასუხი (შეიძლება მეტი დრო დასჭირდეს)",
    value=False
)

if st.button("მიპასუხე") and question.strip():
    ai_key = st.secrets.get("OPENROUTER_API_KEY", "")
    search_key = st.secrets.get("SERPAPI_API_KEY", "")

    if not ai_key:
        st.error("OpenRouter-ის გასაღები ვერ მოიძებნა. შეამოწმე Secrets.")
    else:
        with st.spinner("ნაცარქექია ფიქრობს..."):
            search_context = ""
            results = []

            if use_search:
                if not search_key:
                    st.warning("ძიების გასაღები ვერ მოიძებნა. პასუხს ინტერნეტის გარეშე გავცემ.")
                else:
                    try:
                        response = requests.get(
                            "https://serpapi.com/search.json",
                            params={
                                "engine": "google",
                                "q": question,
                                "api_key": search_key,
                                "hl": "ka",
                                "gl": "ge"
                            },
                            timeout=12
                        )
                        response.raise_for_status()
                        data = response.json()
                        results = data.get("organic_results", [])

                        for item in results[:5]:
                            search_context += (
                                f"\nსათაური: {item.get('title', '')}"
                                f"\nაღწერა: {item.get('snippet', '')}\n"
                            )

                    except requests.exceptions.RequestException:
                        st.warning("ინტერნეტში ძიება ვერ მოხერხდა. პასუხს ძიების გარეშე გავცემ.")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "შენ ხარ ნაცარქექია, მეგობრული და ჭკვიანი ქართული AI ასისტენტი. "
                        "ყოველთვის უპასუხე გამართული, ბუნებრივი ქართულით. "
                        "იყავი გასაგები, ყურადღებიანი და ზუსტი. "
                        "არ მოიგონო ფაქტები. თუ რამე არ იცი, პირდაპირ თქვი."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"მომხმარებლის კითხვა: {question}\n\n"
                        f"ინტერნეტში მოძიებული ინფორმაცია:\n{search_context}\n\n"
                        "მიპასუხე ქართულად, გასაგებად და არსებითად."
                    )
                }
            ]

            try:
                ai_response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {ai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openrouter/free",
                        "messages": messages,
                        "temperature": 0.7
                    },
                    timeout=60
                )

                ai_response.raise_for_status()
                answer = ai_response.json()["choices"][0]["message"]["content"]

                st.subheader("ნაცარქექიას პასუხი")
                st.write(answer)

                if results:
                    st.subheader("გამოყენებული წყაროები")
                    for item in results[:5]:
                        title = item.get("title", "წყარო")
                        link = item.get("link", "")
                        if link:
                            st.markdown(f"- [{title}]({link})")

            except requests.exceptions.Timeout:
                st.error("ნაცარქექიას პასუხის მიღებას დიდი დრო დასჭირდა. სცადე ხელახლა.")
            except requests.exceptions.HTTPError as e:
                st.error(f"AI სერვერის შეცდომა: {e}")
                if e.response is not None:
                    st.code(e.response.text[:1000])
            except Exception as e:
                st.error(f"შეცდომა: {e}")
