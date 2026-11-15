
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


# მოდელების რიგი
MODEL_ORDER = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
]


# ქართული ენის ინსტრუქცია
SYSTEM_PROMPT = (
    "შენ ხარ ნაცარქექია — მეგობრული ქართული AI ასისტენტი. "
    "ყოველთვის უპასუხე გამართული, ბუნებრივი და თანამედროვე ქართულით. "
    "გამოიყენე სწორი ბრუნვები, ზმნის ფორმები, შეთანხმება და სასვენი ნიშნები. "
    "არ თარგმნო ინგლისური გამოთქმები სიტყვასიტყვით. "
    "არ გამოიყენო უაზრო ან გამოგონილი ქართული სიტყვები. "
    "არ აურიო ქართულში სხვა ენები, თუ მომხმარებელი ამას არ ითხოვს. "
    "მარტივ კითხვას მოკლედ უპასუხე, რთულს კი გასაგებად და საჭირო დეტალებით. "
    "არ გაიმეორო ერთი და იგივე აზრი. "
    "არ მოიგონო ფაქტები ან წყაროები. "
    "თუ რამე არ იცი, პირდაპირ თქვი. "
    "პასუხის გაგზავნამდე ჩუმად გადაამოწმე ქართული გრამატიკა და ბუნებრიობა. "
    "აჩვენე მხოლოდ საბოლოო პასუხი ქართულად."
)


def ask_model(api_key, messages):
    errors = []

    for model_name in MODEL_ORDER:

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": (
                        "https://nacarkekia-g5e8maqzmqjwnvswyztvrk.streamlit.app"
                    ),
                    "X-Title": "Nacarkekia",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1200,
                },
                timeout=(8, 60),
            )

            if not response.ok:
                errors.append(
                    f"{model_name}: HTTP {response.status_code} — "
                    f"{response.text[:500]}"
                )
                continue

            data = response.json()
            choices = data.get("choices", [])

            if not choices:
                errors.append(
                    f"{model_name}: პასუხი არ დაბრუნებულა."
                )
                continue

            choice = choices[0]
            message = choice.get("message") or {}
            answer = message.get("content")

            if isinstance(answer, list):
                answer = "\n".join(
                    part.get("text", "")
                    for part in answer
                    if isinstance(part, dict) and part.get("text")
                )

            if isinstance(answer, str) and answer.strip():
                return (
                    answer.strip(),
                    data.get("model", model_name),
                    choice.get("finish_reason"),
                    errors,
                )

            errors.append(
                f"{model_name}: ცარიელი პასუხი. "
                f"დასრულების მიზეზი: {choice.get('finish_reason')}"
            )

        except requests.exceptions.Timeout:
            errors.append(
                f"{model_name}: მოთხოვნას დრო გაუვიდა."
            )

        except requests.exceptions.RequestException as error:
            errors.append(
                f"{model_name}: კავშირის შეცდომა — {error}"
            )

        except ValueError:
            errors.append(
                f"{model_name}: სერვერის პასუხი JSON ფორმატში არ არის."
            )

    return None, None, None, errors


if st.button("მიპასუხე") and question.strip():

    ai_key = st.secrets.get("OPENROUTER_API_KEY", "")
    search_key = st.secrets.get("SERPAPI_API_KEY", "")

    if not ai_key:
        st.error(
            "OpenRouter-ის გასაღები ვერ მოიძებნა. "
            "შეამოწმე Streamlit Secrets."
        )
        st.stop()

    with st.spinner("ნაცარქექია ფიქრობს..."):

        started_at = time.monotonic()
        search_context = ""
        results = []

        # ინტერნეტძიება
        if use_search and search_key:

            try:
                search_response = requests.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google",
                        "q": question,
                        "api_key": search_key,
                        "hl": "ka",
                        "gl": "ge",
                    },
                    timeout=(5, 12),
                )

                search_response.raise_for_status()
                search_data = search_response.json()

                results = search_data.get(
                    "organic_results",
                    []
                )

                for item in results[:5]:
                    search_context += (
                        f"\nსათაური: {item.get('title', '')}\n"
                        f"აღწერა: {item.get('snippet', '')}\n"
                    )

            except requests.exceptions.RequestException:
                st.warning(
                    "ინტერნეტში ძიება ვერ დასრულდა. "
                    "პასუხს ძიების გარეშე გავაგრძელებ."
                )

        elif use_search and not search_key:
            st.warning(
                "ძიების გასაღები ვერ მოიძებნა. "
                "პასუხს ძიების გარეშე გავაგრძელებ."
            )

        # შეტყობინებების მომზადება
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        messages.extend(
            st.session_state.chat_history[-8:]
        )

        user_message = (
            f"მომხმარებლის კითხვა:\n{question}\n\n"
            f"ინტერნეტში მოძიებული ინფორმაცია:\n{search_context}\n\n"
            "მიპასუხე გამართული, ბუნებრივი ქართულით."
        )

        messages.append({
            "role": "user",
            "content": user_message,
        })

        # პირველ და მეორე მოდელზე ცდა
        answer, used_model, finish_reason, errors = ask_model(
            ai_key,
            messages
        )

        if not answer:

            st.error(
                "ნაცარქექიამ პასუხი ვერ მიიღო. "
                "ორივე უფასო მოდელი მიუწვდომელია ან მოთხოვნის ლიმიტი ამოიწურა."
            )

            st.caption("ტექნიკური დეტალები:")
            for error in errors:
                st.code(error)

            st.stop()

        # პასუხის ჩვენება
        st.subheader("ნაცარქექიას პასუხი")
        st.write(answer)

        if finish_reason == "length":
            st.warning(
                "პასუხი შესაძლოა ბოლომდე არ დასრულებულა."
            )

        # საუბრის მეხსიერებაში შენახვა
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_message,
        })

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
        })

        st.session_state.chat_history = (
            st.session_state.chat_history[-8:]
        )

        # დრო და გამოყენებული მოდელი
        elapsed = time.monotonic() - started_at

        st.caption(
            f"პასუხის დრო: {elapsed:.1f} წამი | "
            f"მოდელი: {used_model}"
        )

        # გამოყენებული წყაროები
        if results:

            st.subheader("გამოყენებული წყაროები")

            for item in results[:5]:

                title = item.get("title", "წყარო")
                link = item.get("link", "")

                if link:
                    st.markdown(
                        f"- [{title}]({link})"
                    )

