
import streamlit as st
import requests

st.set_page_config(
    page_title="ნაცარქექია",
    page_icon="🧠"
)

st.title("🧠 ნაცარქექია")
st.write("შენი პირადი ქართული AI ასისტენტი.")

# საუბრის მეხსიერება
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input("მკითხე რამე:")

use_search = st.checkbox(
    "ინტერნეტშიც მოძებნე პასუხი",
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

            # ინტერნეტში ძიება
            if use_search and search_key:
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
                    search_data = response.json()
                    results = search_data.get("organic_results", [])

                    for item in results[:5]:
                        search_context += (
                            f"\nსათაური: {item.get('title', '')}\n"
                            f"აღწერა: {item.get('snippet', '')}\n"
                        )

                except requests.exceptions.RequestException:
                    st.warning("ინტერნეტში ძიება ვერ მოხერხდა.")

            elif use_search and not search_key:
                st.warning("ძიების გასაღები ვერ მოიძებნა.")

            # AI-ს ინსტრუქცია
            messages = [
                {
                    "role": "system",
                    "content": (
                        "შენ ხარ ნაცარქექია — მეგობრული ქართული AI ასისტენტი. "
                        "ყოველთვის უპასუხე გამართული, ბუნებრივი ქართულით. "
                        "გამოიყენე სწორი გრამატიკა და სასვენი ნიშნები. "
                        "არ აურიო ქართულში სხვა ენები, თუ ამას მომხმარებელი "
                        "სპეციალურად არ ითხოვს. "
                        "არ გაიმეორო ერთი და იგივე აზრი. "
                        "უპასუხე გასაგებად და შინაარსიანად. "
                        "არ მოიგონო ფაქტები. თუ რამე არ იცი, პირდაპირ თქვი."
                    )
                }
            ]

            # წინა საუბრის დამატება
            messages.extend(st.session_state.chat_history)

            # მიმდინარე კითხვის დამატება
            user_message = (
                f"მომხმარებლის კითხვა: {question}\n\n"
                f"ინტერნეტში მოძიებული ინფორმაცია:\n"
                f"{search_context}\n\n"
                "მიპასუხე გამართული ქართულით."
            )

            messages.append({
                "role": "user",
                "content": user_message
            })

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
                        "temperature": 0.3,
                        "max_tokens": 1200
                    },
                    timeout=60
                )

                ai_response.raise_for_status()
                data = ai_response.json()

                choices = data.get("choices", [])

                if not choices:
                    st.error("AI-მ პასუხი ვერ დააბრუნა.")
                    st.code(str(data)[:1500])
                    st.stop()

                answer = choices[0].get("message", {}).get("content")

                if not isinstance(answer, str) or not answer.strip():
                    st.error("AI-მ ცარიელი პასუხი დააბრუნა.")
                    st.code(str(data)[:1500])
                    st.stop()

                # პასუხის ჩვენება
                st.subheader("ნაცარქექიას პასუხი")
                st.write(answer)

                # საუბრის მეხსიერებაში შენახვა
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_message
                })

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

                # ბოლო 12 შეტყობინების დატოვება
                st.session_state.chat_history = (
                    st.session_state.chat_history[-12:]
                )

                # გამოყენებული წყაროები
                if results:
                    st.subheader("გამოყენებული წყაროები")

                    for item in results[:5]:
                        title = item.get("title", "წყარო")
                        link = item.get("link", "")

                        if link:
                            st.markdown(f"- [{title}]({link})")

            except requests.exceptions.Timeout:
                st.error("პასუხის მიღებას დიდი დრო დასჭირდა. სცადე ხელახლა.")

            except requests.exceptions.HTTPError as e:
                st.error(f"AI სერვერის შეცდომა: {e}")

                if e.response is not None:
                    st.code(e.response.text[:1500])

            except requests.exceptions.RequestException as e:
                st.error(f"კავშირის შეცდომა: {e}")

            except Exception as e:
                st.error(f"შეცდომა: {e}")

