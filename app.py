
import time

import requests
import streamlit as st

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
            started_at = time.monotonic()
            search_context = ""
            results = []

            # ინტერნეტში ძიება
            if use_search and search_key:
                try:
                    search_response = requests.get(
                        "https://serpapi.com/search.json",
                        params={
                            "engine": "google",
                            "q": question,
                            "api_key": search_key,
                            "hl": "ka",
                            "gl": "ge"
                        },
                        timeout=(5, 8)
                    )
                    search_response.raise_for_status()
                    search_data = search_response.json()
                    results = search_data.get("organic_results", [])

                    for item in results[:5]:
                        search_context += (
                            f"\nსათაური: {item.get('title', '')}\n"
                            f"აღწერა: {item.get('snippet', '')}\n"
                        )

                except requests.exceptions.RequestException:
                    st.warning(
                        "ინტერნეტში ძიება დროულად ვერ დასრულდა. "
                        "პასუხს ძიების გარეშე გავაგრძელებ."
                    )

            elif use_search and not search_key:
                st.warning(
                    "ძიების გასაღები ვერ მოიძებნა. "
                    "პასუხს ძიების გარეშე გავაგრძელებ."
                )

            system_prompt = (
                "შენ ხარ ნაცარქექია — მეგობრული ქართული AI ასისტენტი. "
                "ყოველთვის უპასუხე გამართული, ბუნებრივი ქართულით. "
                "გამოიყენე სწორი გრამატიკა და სასვენი ნიშნები. "
                "არ აურიო ქართულში სხვა ენები, თუ მომხმარებელი ამას "
                "სპეციალურად არ ითხოვს. "
                "არ გაიმეორო ერთი და იგივე აზრი. "
                "უპასუხე პირდაპირ და გასაგებად. "
                "მარტივ კითხვაზე მოკლედ უპასუხე, რთულზე კი საჭირო დეტალები დაამატე. "
                "არ მოიგონო ფაქტები. თუ რამე არ იცი, პირდაპირ თქვი. "
                "მომხმარებელს აჩვენე მხოლოდ საბოლოო პასუხი."
            )

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]

            # ბოლო 8 შეტყობინება
            messages.extend(st.session_state.chat_history[-8:])

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
                        "max_tokens": 900
                    },
                    timeout=(8, 45)
                )

                ai_response.raise_for_status()
                data = ai_response.json()

                if data.get("error"):
                    st.error("AI სერვერმა შეცდომა დააბრუნა.")
                    st.code(str(data["error"])[:1200])
                    st.stop()

                choices = data.get("choices", [])

                if not choices:
                    st.error(
                        "AI-მ პასუხი ვერ დააბრუნა. "
                        "სცადე ხელახლა რამდენიმე წამში."
                    )
                    st.code(str(data)[:1200])
                    st.stop()

                choice = choices[0]
                message = choice.get("message") or {}
                answer = message.get("content")
                finish_reason = choice.get("finish_reason")

                if isinstance(answer, list):
                    answer = "\n".join(
                        part.get("text", "")
                        for part in answer
                        if isinstance(part, dict) and part.get("text")
                    )

                if not isinstance(answer, str) or not answer.strip():
                    if finish_reason == "length":
                        st.error(
                            "მოდელმა პასუხი ვერ დაასრულა. "
                            "სცადე კითხვა უფრო მოკლედ დასვა."
                        )
                    else:
                        st.error(
                            "AI-მ ტექსტური პასუხი არ დააბრუნა. "
                            "სერვერი შესაძლოა დატვირთულია — სცადე ხელახლა."
                        )

                    st.caption(
                        f"მოდელი: {data.get('model', 'უცნობია')} | "
                        f"დასრულების მიზეზი: {finish_reason}"
                    )
                    st.stop()

                # პასუხის ჩვენება
                st.subheader("ნაცარქექიას პასუხი")
                st.write(answer)

                # მეხსიერებაში შენახვა
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_message
                })

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

                st.session_state.chat_history = (
                    st.session_state.chat_history[-8:]
                )

                # პასუხის დრო და მოდელი
                elapsed = time.monotonic() - started_at
                st.caption(
                    f"პასუხის დრო: {elapsed:.1f} წამი | "
                    f"მოდელი: {data.get('model', 'უცნობია')}"
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
                st.error(
                    "AI-მ 45 წამში პასუხი ვერ დააბრუნა. "
                    "უფასო სერვერი შესაძლოა გადატვირთულია. "
                    "ცოტა ხანში სცადე ხელახლა."
                )

            except requests.exceptions.HTTPError as e:
                st.error(f"AI სერვერის შეცდომა: {e}")

                if e.response is not None:
                    st.code(e.response.text[:1200])

            except requests.exceptions.RequestException as e:
                st.error(f"კავშირის შეცდომა: {e}")

            except Exception as e:
                st.error(f"შეცდომა: {e}")


