
import streamlit as st
import requests

st.set_page_config(page_title="ნაცარქექია", page_icon="🧠")

st.title("🧠 ნაცარქექია")
st.write("შენი პირადი ქართული AI ასისტენტი.")

question = st.text_input("მკითხე რამე:")

if st.button("მიპასუხე") and question:
    search_key = st.secrets.get("SERPAPI_API_KEY", "")
    ai_key = st.secrets.get("OPENROUTER_API_KEY", "")

    if not ai_key:
        st.error("OpenRouter-ის გასაღები ვერ მოიძებნა. შეამოწმე Secrets.")
    else:
        with st.spinner("ნაცარქექია ფიქრობს..."):
            try:
                search_context = ""

                if search_key:
                    search_response = requests.get(
                        "https://serpapi.com/search.json",
                        params={
                            "engine": "google",
                            "q": question,
                            "api_key": search_key,
                            "hl": "ka",
                            "gl": "ge"
                        },
                        timeout=20
                    )
                    search_response.raise_for_status()
                    search_data = search_response.json()

                    results = search_data.get("organic_results", [])

                    for item in results[:5]:
                        search_context += (
                            f"\nსათაური: {item.get('title', '')}"
                            f"\nაღწერა: {item.get('snippet', '')}"
                            f"\nბმული: {item.get('link', '')}\n"
                        )

                messages = [
                    {
                        "role": "system",
                        "content": (
                           "შენ ხარ ნაცარქექია, მეგობრული და ჭკვიანი AI ასისტენტი. "
"ყოველთვის უპასუხე იმავე ენაზე, რომელზეც მომხმარებელი გწერს. "
"თუ ქართულად გწერს, უპასუხე ქართულად; თუ ინგლისურად — ინგლისურად; "
"თუ რუსულად — რუსულად. სხვა ენებზეც იგივე წესი დაიცავი. "
"უპასუხე ბუნებრივად, გამართულად და გასაგებად. "
"არ მოიგონო ფაქტები."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"კითხვა: {question}\n\n"
                            f"ინტერნეტში მოძიებული ინფორმაცია:\n{search_context}\n\n"
                           "შემიდგინე გასაგები პასუხი იმავე ენაზე, რომელზეც მომხმარებელი მეკითხება."
                        )
                    }
                ]

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
                    timeout=90
                )

                ai_response.raise_for_status()
                answer = ai_response.json()["choices"][0]["message"]["content"]

                st.subheader("ნაცარქექიას პასუხი")
                st.write(answer)

                if results if search_key else False:
                    st.subheader("გამოყენებული წყაროები")
                    for item in results[:5]:
                        title = item.get("title", "წყარო")
                        link = item.get("link", "")
                        if link:
                            st.markdown(f"- [{title}]({link})")

            except requests.exceptions.HTTPError as e:
                st.error(f"სერვერის შეცდომა: {e}")
                if e.response is not None:
                    st.code(e.response.text[:1000])
            except Exception as e:
                st.error(f"შეცდომა: {e}")


