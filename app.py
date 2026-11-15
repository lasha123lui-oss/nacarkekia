
import json
import time

import requests
import streamlit as st


st.set_page_config(page_title="ნაცარქექია", page_icon="🧠")
st.title("🧠 ნაცარქექია")
st.write("შენი პირადი ქართული AI ასისტენტი.")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ვინარჩუნებთ წინა მოდელების სიას.
# უფასო მოდელების ხელმისაწვდომობა შეიძლება შეიცვალოს.
MODEL_ORDER = [
    "inclusionai/ling-3.2-flash:free",
    "baidu/ernie-5.5-flash-preview:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "dots-studio/dots-3-note-preview:free",
]

SYSTEM_PROMPT = """
შენ ხარ ნაცარქექია — მეგობრული ქართული AI ასისტენტი.
უპასუხე გამართული, ბუნებრივი და თანამედროვე ქართულით.
გამოიყენე სწორი ბრუნვები, ზმნის ფორმები და სასვენი ნიშნები.
არ თარგმნო ინგლისური გამოთქმები სიტყვასიტყვით.
არ გამოიყენო უაზრო ან გამოგონილი ქართული სიტყვები.
მარტივ კითხვას მოკლედ უპასუხე, რთულს კი გასაგებად.
არ მოიგონო ფაქტები, წყაროები ან ციტატები.
თუ რამე არ იცი, პირდაპირ თქვი.
აჩვენე მხოლოდ საბოლოო პასუხი ქართულად.
""".strip()

REVIEW_PROMPT = """
შენ ხარ ქართული ტექსტის რედაქტორი.
გაასწორე გრამატიკა, სიტყვათა შეთანხმება და არაბუნებრივი გამოთქმები.
შეინარჩუნე საწყისი აზრი და ფაქტები.
არ დაამატო ახალი ინფორმაცია.
თუ პასუხი შეწყვეტილია, დაასრულე მხოლოდ მაშინ, თუ აზრი ნათელია.
დააბრუნე მხოლოდ საბოლოო გამართული პასუხი.
""".strip()

MEMORY_PROMPT = """
შენ ხარ პირადი ასისტენტის მეხსიერების დამგეგმავი.

შეამოწმე მომხმარებლის ბოლო შეტყობინება და ამოარჩიე მაქსიმუმ
3 მნიშვნელოვანი ფაქტი, რომლის დამახსოვრებაც მომავალ საუბრებში
შეიძლება სასარგებლო იყოს.

დაიმახსოვრე მხოლოდ მომხმარებლის მიერ პირდაპირ ნათქვამი ფაქტები:
- ხანგრძლივი ინტერესები და ჰობი;
- მიმდინარე პროექტები და მიზნები;
- სტაბილური უპირატესობები;
- მომხმარებლის მიერ ნათქვამი პრაქტიკული გარემოებები.

არ შეინახო:
- პაროლები, API გასაღებები, საიდუმლო კოდები;
- საბანკო ან საიდენტიფიკაციო მონაცემები;
- ჯანმრთელობის, რელიგიის, პოლიტიკური შეხედულებების,
  სექსუალური ცხოვრების ან სხვა მგრძნობიარე პირადი ინფორმაცია;
- დროებითი კითხვები, ვარაუდები ან სხვის შესახებ ინფორმაცია;
- ფაქტი, რომელიც მომხმარებელს პირდაპირ არ უთქვამს.

არ გამოიტანო დასკვნა და არ მოიგონო ინფორმაცია.
თუ დასამახსოვრებელი არაფერია, დააბრუნე ცარიელი სია.

პასუხი დააბრუნე მხოლოდ JSON ფორმატში:
{"memories": ["პირველი ფაქტი", "მეორე ფაქტი"]}

ჩანაწერები უნდა იყოს მოკლე, გასაგები და ქართულად.
""".strip()


def memory_config():
    url = st.secrets.get("SUPABASE_URL", "").strip().rstrip("/")
    key = st.secrets.get("SUPABASE_SECRET_KEY", "").strip()
    owner = st.secrets.get("MEMORY_OWNER_ID", "").strip()
    return url, key, owner


def memory_request(method, params=None, payload=None):
    url, key, owner = memory_config()

    if not url or not key or not owner:
        raise RuntimeError(
            "Supabase-ის Secrets სრულად შევსებული არ არის."
        )

    # ახალი sb_secret გასაღები იგზავნება მხოლოდ apikey სათაურში.
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
    }

    endpoint = f"{url}/rest/v1/nacarkekia_memory"
    query = {"owner_id": f"eq.{owner}"}

    if params:
        query.update(params)

    if method == "POST":
        headers["Prefer"] = "return=minimal"
        response = requests.post(
            endpoint,
            headers=headers,
            params=query,
            json=payload,
            timeout=15,
        )
    elif method == "GET":
        response = requests.get(
            endpoint,
            headers=headers,
            params=query,
            timeout=15,
        )
    elif method == "DELETE":
        response = requests.delete(
            endpoint,
            headers=headers,
            params=query,
            timeout=15,
        )
    else:
        raise ValueError("მეხსიერების მოქმედება უცნობია.")

    if not response.ok:
        raise RuntimeError(
            f"მეხსიერების ბაზის შეცდომა: "
            f"HTTP {response.status_code} {response.text[:250]}"
        )

    if method == "GET":
        return response.json()

    return True


def get_memories():
    return memory_request(
        "GET",
        params={
            "select": "id,memory,created_at",
            "order": "created_at.desc",
            "limit": "100",
        },
    )


def save_memory(value):
    _, _, owner = memory_config()

    return memory_request(
        "POST",
        payload={
            "owner_id": owner,
            "memory": value,
        },
    )


def delete_memory(memory_id):
    return memory_request(
        "DELETE",
        params={"id": f"eq.{memory_id}"},
    )


def call_model(api_key, model_name, messages, max_tokens=1400):
    response = requests.post(
        API_URL,
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
            "temperature": 0.25,
            "max_tokens": max_tokens,
        },
        timeout=(8, 35),
    )

    if not response.ok:
        try:
            detail = response.json().get(
                "error", {}
            ).get("message", response.text)
        except ValueError:
            detail = response.text

        raise RuntimeError(
            f"HTTP {response.status_code}: {str(detail)[:300]}"
        )

    data = response.json()
    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError("მოდელმა პასუხი არ დააბრუნა.")

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
            errors.append(
                f"{model_name}: {str(error)[:250]}"
            )

    return None, None, None, errors


def suggest_memories(api_key, model_name, user_text, existing_memories):
    """ამოიცნობს შესაძლო ფაქტებს, მაგრამ არაფერს ინახავს."""

    messages = [
        {"role": "system", "content": MEMORY_PROMPT},
        {
            "role": "user",
            "content": (
                f"მომხმარებლის შეტყობინება:\n{user_text}\n\n"
                f"უკვე შენახული ფაქტები:\n{existing_memories}\n\n"
                "არ გაიმეორო უკვე შენახული ფაქტები."
            ),
        },
    ]

    result, _, _ = call_model(
        api_key,
        model_name,
        messages,
        max_tokens=350,
    )

    # ვცდილობთ JSON-ის ამოღებას იმ შემთხვევაშიც,
    # თუ მოდელმა ზედმეტი ტექსტი დაუმატა.
    start = result.find("{")
    end = result.rfind("}")

    if start == -1 or end <= start:
        return []

    try:
        data = json.loads(result[start:end + 1])
    except json.JSONDecodeError:
        return []

    candidates = data.get("memories", [])

    if not isinstance(candidates, list):
        return []

    clean = []

    for item in candidates[:3]:
        if not isinstance(item, str):
            continue

        item = item.strip()

        if not item or len(item) > 250:
            continue

        if any(item.casefold() == old.casefold()
               for old in existing_memories):
            continue

        clean.append(item)

    return clean


# სესიის ცვლადები
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_memories" not in st.session_state:
    st.session_state.pending_memories = []

if "memory_notice" not in st.session_state:
    st.session_state.memory_notice = ""


# მეხსიერების გვერდითი პანელი
st.sidebar.header("🧠 ნაცარქექიას მეხსიერება")
st.sidebar.caption(
    "აქ შეგიძლია თავად დაამატო ინფორმაცია, "
    "რომელიც ნაცარქექიამ უნდა დაიმახსოვროს."
)

memory_text = st.sidebar.text_area(
    "რა დაიმახსოვროს?",
    placeholder="მაგალითად: ჩემი საყვარელი თამაშია PUBG.",
)

if st.sidebar.button("მეხსიერებაში შენახვა"):
    if memory_text.strip():
        try:
            save_memory(memory_text.strip())
            st.sidebar.success("ინფორმაცია შენახულია.")
            st.rerun()
        except Exception as error:
            st.sidebar.error(str(error))
    else:
        st.sidebar.warning("ჯერ ჩაწერე ინფორმაცია.")


# ბაზიდან მეხსიერების წამოღება
try:
    memories = get_memories()
    memory_ready = True
    st.sidebar.caption(
        f"შენახულია {len(memories)} ჩანაწერი"
    )

    for item in memories:
        with st.sidebar.expander(item["memory"][:55]):
            st.write(item["memory"])

            if st.button(
                "წაშლა",
                key=f"delete_memory_{item['id']}",
            ):
                try:
                    delete_memory(item["id"])
                    st.rerun()
                except Exception as error:
                    st.sidebar.error(str(error))

except Exception as error:
    memories = []
    memory_ready = False
    st.sidebar.warning(
        "მეხსიერების ბაზასთან კავშირი ვერ შედგა."
    )
    st.sidebar.caption(str(error)[:250])


# მომხმარებლის თანხმობის მოლოდინში არსებული ფაქტები
if st.session_state.memory_notice:
    st.success(st.session_state.memory_notice)
    st.session_state.memory_notice = ""

if st.session_state.pending_memories:
    st.subheader("🧠 ნაცარქექიას შემოთავაზება")
    st.write(
        "ეს ინფორმაცია შეიძლება მომავალში გამოგვადგეს. "
        "შენ გადაწყვიტე, დავიმახსოვრო თუ არა."
    )

    for index, candidate in enumerate(
        st.session_state.pending_memories
    ):
        st.write(f"• {candidate}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "დამახსოვრება",
                key=f"approve_memory_{index}",
                use_container_width=True,
            ):
                try:
                    save_memory(candidate)
                    st.session_state.pending_memories.pop(index)
                    st.session_state.memory_notice = (
                        "ინფორმაცია წარმატებით დავიმახსოვრე."
                    )
                    st.rerun()
                except Exception as error:
                    st.error(str(error))

        with col2:
            if st.button(
                "არ შეინახო",
                key=f"reject_memory_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_memories.pop(index)
                st.rerun()

    if st.button("ყველა შემოთავაზებაზე უარი"):
        st.session_state.pending_memories = []
        st.rerun()


# ჩატის პარამეტრები
question = st.text_input("მკითხე რამე:")
use_search = st.checkbox(
    "ინტერნეტშიც მოძებნე პასუხი",
    value=False,
)
check_quality = st.checkbox(
    "პასუხი ქართულად გადაამოწმე",
    value=True,
)


if st.button("მიპასუხე") and question.strip():
    ai_key = st.secrets.get("OPENROUTER_API_KEY", "")
    search_key = st.secrets.get("SERPAPI_API_KEY", "")

    if not ai_key:
        st.error(
            "OpenRouter-ის გასაღები ვერ მოიძებნა."
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
                    "organic_results", []
                )

                for item in results[:5]:
                    search_context += (
                        f"\nსათაური: {item.get('title', '')}\n"
                        f"აღწერა: {item.get('snippet', '')}\n"
                    )

            except (
                requests.exceptions.RequestException,
                ValueError,
            ):
                st.warning("ინტერნეტძიება ვერ შესრულდა.")

        elif use_search and not search_key:
            st.warning(
                "SerpApi-ის გასაღები ვერ მოიძებნა."
            )

        # შენახული მეხსიერების კონტექსტი
        memory_context = "\n".join(
            f"- {item['memory']}"
            for item in memories
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        if memory_context:
            messages.append({
                "role": "system",
                "content": (
                    "ქვემოთ მოცემულია მომხმარებლის მიერ "
                    "თანხმობით შენახული მეხსიერება. გამოიყენე "
                    "მხოლოდ მაშინ, როცა კითხვას ეხება:\n"
                    + memory_context
                ),
            })

        messages.extend(
            st.session_state.chat_history[-8:]
        )

        user_message = (
            f"მომხმარებლის კითხვა:\n{question}\n\n"
            f"ინტერნეტში მოძიებული ინფორმაცია:\n"
            f"{search_context}\n\n"
            "მიპასუხე გამართული, ბუნებრივი ქართულით."
        )

        messages.append({
            "role": "user",
            "content": user_message,
        })

        answer, used_model, finish_reason, errors = ask_models(
            ai_key,
            messages,
        )

        if not answer:
            st.error(
                "უფასო მოდელები ამჟამად მიუწვდომელია."
            )

            for error in errors:
                st.code(error)

            st.stop()

        # ქართული ტექსტის შემოწმება
        quality_checked = False

        if check_quality:
            with st.spinner("ქართულს ვამოწმებ..."):
                try:
                    reviewed, _, _ = call_model(
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
                                    f"კითხვა:\n{question}\n\n"
                                    f"პასუხი:\n{answer}"
                                ),
                            },
                        ],
                        max_tokens=1500,
                    )

                    answer = reviewed
                    quality_checked = True

                except (
                    requests.exceptions.RequestException,
                    ValueError,
                    RuntimeError,
                ):
                    pass

        st.subheader("ნაცარქექიას პასუხი")
        st.write(answer)

        if finish_reason == "length":
            st.warning(
                "პასუხი შესაძლოა ბოლომდე არ დასრულებულა."
            )

        if quality_checked:
            st.caption(
                "ქართული ტექსტი დამატებით შემოწმებულია."
            )

        # საუბრის ისტორია
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

        # ავტომატური მეხსიერების შეთავაზება.
        # აქ ხდება მხოლოდ ამოცნობა — შენახვა არა.
        if memory_ready:
            try:
                existing_texts = [
                    item["memory"] for item in memories
                ]

                candidates = suggest_memories(
                    ai_key,
                    used_model,
                    question,
                    existing_texts,
                )

                if candidates:
                    st.session_state.pending_memories = (
                        candidates
                    )

            except (
                requests.exceptions.RequestException,
                ValueError,
                RuntimeError,
            ):
                pass

        elapsed = time.monotonic() - started_at

        st.caption(
            f"პასუხის დრო: {elapsed:.1f} წამი | "
            f"მოდელი: {used_model}"
        )

        # წყაროები
        if results:
            st.subheader("გამოყენებული წყაროები")

            for item in results[:5]:
                title = item.get("title", "წყარო")
                link = item.get("link", "")

                if link:
                    st.markdown(
                        f"- [{title}]({link})"
                    )

    # შემოთავაზებების გამოსაჩენად განახლება
    if st.session_state.pending_memories:
        st.rerun()
