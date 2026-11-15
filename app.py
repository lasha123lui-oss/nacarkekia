
import time

import requests
import streamlit as st


st.set_page_config(page_title="ნაცარქექია", page_icon="🧠")

st.title("🧠 ნაცარქექია")
st.write("შენი პირადი ქართული AI ასისტენტი.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input("მკითხე რამე:")

use_search = st.checkbox("ინტერნეტშიც მოძებნე პასუხი", value=False)
check_quality = st.checkbox("პასუხი ქართულად გადაამოწმე", value=True)

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_ORDER = [
    "inclusionai/ling-3.2-flash:free",
    "baidu/ernie-5.5-flash-preview:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "dots-studio/dots-3-note-preview:free",
]

SYSTEM_PROMPT = """
შენ ხარ ნაცარქექია — მეგობრული ქართული AI ასისტენტი.
უპასუხე გამართული, ბუნებრივი და თანამედროვე ქართულით.
გამოიყენე სწორი ბრუნვები, ზმნის ფორმები, შეთანხმება და სასვენი ნიშნები.
არ თარგმნო ინგლისური გამოთქმები სიტყვასიტყვით.
არ გამოიყენო უაზრო ან გამოგონილი ქართული სიტყვები.
არ აურიო ქართულში სხვა ენები, თუ მომხმარებელი ამას არ ითხოვს.
მარტივ კითხვას მოკლედ უპასუხე, რთულს კი გასაგებად და საჭირო დეტალებით.
არ გაიმეორო ერთი და იგივე აზრი.
არ მოიგონო ფაქტები, წყაროები ან ციტატები.
თუ რამე არ იცი, პირდაპირ თქვი.
მოძიებული ინფორმაციის გამოყენებისას განასხვავე ფაქტი და ვარაუდი.
აჩვენე მხოლოდ საბოლოო პასუხი ქართულად.
""".strip()

REVIEW_PROMPT = """
შენ ხარ ქართული ტექსტის მკაცრი, მაგრამ ფრთხილი რედაქტორი.
შეამოწმე ქვემოთ მოცემული AI პასუხი:
1. გამართულია თუ არა ქართული გრამატიკა და სიტყვათა შეთანხმება;
2. ბუნებრივად ჟღერს თუ არა ტექსტი ქართულად;
3. ხომ არ არის აზრი დამახინჯებული, წინააღმდეგობრივი ან გაუგებარი;
4. ხომ არ არის წინადადება შეწყვეტილი ან პასუხი დაუსრულებელი;
5. ხომ არ არის გამოგონილი ფაქტი ან წყარო.

თუ პასუხი კარგია, დააბრუნე უცვლელად.
თუ შეცდომებია, გაასწორე ისე, რომ საწყისი აზრი და ფაქტები შეინარჩუნო.
არ დაამატო ახალი ფაქტები და არ გაახანგრძლივო პასუხი უმიზეზოდ.
დააბრუნე მხოლოდ საბოლოო, გამართული პასუხი — კომენტარებისა და შეფასების გარეშე.
""".strip()


def call_model(api_key, model_name, messages, max_tokens=1400):
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nacarkekia-g5e8maqzmqjwnvswyztvrk.streamlit.app",
            "X-Title": "Nacarkekia",
        },
        json={
            "model": model_name,
            "messages": messages,
            "temperature": 0.25,
            "max_tokens": max_tokens,
        },
        timeout=(8, 35),
    )

    if not response.ok:
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get(
                "message", response.text
            )
        except ValueError:
            error_message = response.text

        raise RuntimeError(
            f"HTTP {response.status_code}: {str(error_message)[:300]}"
        )

    data = response.json()
    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError("სერვერმა პასუხის არჩევანი არ დააბრუნა.")

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
        raise RuntimeError(
            f"ცარიელი პასუხი (finish_reason: {finish_reason})."
        )

    return answer.strip(), data.get("model", model_name), finish_reason


def ask_models(api_key, messages):
    errors = []

    for model_name in MODEL_ORDER:
        try:
            answer, actual_model, finish_reason = call_model(
                api_key, model_name, messages
            )
            return answer, actual_model, finish_reason, errors

        except (
            requests.exceptions.RequestException,
            ValueError,
            RuntimeError,
        ) as error:
            errors.append(f"{model_name}: {str(error)[:300]}")

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
                results = search_data.get("organic_results", [])

                for item in results[:5]:
                    search_context += (
                        f"\nსათაური: {item.get('title', '')}\n"
                        f"აღწერა: {item.get('snippet', '')}\n"
                    )

            except (
                requests.exceptions.RequestException,
                ValueError,
            ):
                st.warning(
                    "ინტერნეტში ძიება ვერ დასრულდა. "
                    "პასუხს მოძიებული ინფორმაციის გარეშე გავაგრძელებ."
                )

        elif use_search and not search_key:
            st.warning(
                "SerpApi-ის გასაღები ვერ მოიძებნა. "
                "პასუხს ინტერნეტძიების გარეშე გავაგრძელებ."
            )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        messages.extend(st.session_state.chat_history[-8:])

        user_message = (
            f"მომხმარებლის კითხვა:\n{question}\n\n"
            f"ინტერნეტში მოძიებული ინფორმაცია:\n{search_context}\n\n"
            "მიპასუხე გამართული, ბუნებრივი ქართულით."
        )

        messages.append({
            "role": "user",
            "content": user_message,
        })

        answer, used_model, finish_reason, errors = ask_models(
            ai_key, messages
        )

        if not answer:
            st.error(
                "ნაცარქექიამ პასუხი ვერ მიიღო. "
                "უფასო მოდელები შეიძლება დროებით მიუწვდომელი "
                "ან გადატვირთული იყოს."
            )

            st.caption("მოდელების შეცდომები:")
            for error in errors:
                st.code(error)

            st.info(
                "ცოტა ხანში სცადე ხელახლა. "
                "უფასო მოდელებს გამოყენების ლიმიტები აქვთ."
            )
            st.stop()

        quality_checked = False
        review_error = None

        if check_quality:
            with st.spinner("პასუხის ქართულს ვამოწმებ..."):
                try:
                    reviewed, _, review_finish = call_model(
                        ai_key,
                        used_model,
                        [
                            {
                                "role": "system",
                                "content": REVIEW_PROMPT,
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"მომხმარებლის კითხვა:\n{question}\n\n"
                                    f"მოსამოწმებელი პასუხი:\n{answer}"
                                ),
                            },
                        ],
                        max_tokens=1500,
                    )

                    if reviewed.strip():
                        answer = reviewed.strip()
                        quality_checked = True

                    if review_finish == "length":
                        review_error = (
                            "შემოწმების პასუხი შესაძლოა ბოლომდე "
                            "არ დასრულებულა."
                        )

                except (
                    requests.exceptions.RequestException,
                    ValueError,
                    RuntimeError,
                ) as error:
                    review_error = str(error)[:300]

        st.subheader("ნაცარქექიას პასუხი")
        st.write(answer)

        if finish_reason == "length":
            st.warning("პასუხი შესაძლოა ბოლომდე არ დასრულებულა.")

        if quality_checked:
            st.caption("ქართული ტექსტი დამატებით შემოწმებულია.")

        elif check_quality and review_error:
            st.warning(
                "პასუხის დამატებითი შემოწმება ვერ შესრულდა; "
                "ნაჩვენებია საწყისი პასუხი."
            )
            st.caption(review_error)

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

        elapsed = time.monotonic() - started_at

        st.caption(
            f"პასუხის დრო: {elapsed:.1f} წამი | "
            f"მოდელი: {used_model}"
        )

        if results:
            st.subheader("გამოყენებული წყაროები")

            for item in results[:5]:
                title = item.get("title", "წყარო")
                link = item.get("link", "")

                if link:
                    st.markdown(f"- [{title}]({link})")
