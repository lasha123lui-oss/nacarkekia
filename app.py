
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st


# --------------------------------------------------
# ძირითადი პარამეტრები
# --------------------------------------------------

st.set_page_config(page_title="ნაცარქექია", page_icon="🧠")
st.title("🧠 ნაცარქექია")
st.write("შენი პირადი ქართული AI ასისტენტი.")

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
გამოიყენე სწორი ბრუნვები, ზმნის ფორმები და სასვენი ნიშნები.
არ თარგმნო ინგლისური გამოთქმები სიტყვასიტყვით.
არ მოიგონო ფაქტები, წყაროები ან ციტატები.
თუ რამე არ იცი, პირდაპირ თქვი.
მარტივ კითხვას მოკლედ უპასუხე, რთულს კი გასაგებად.
აჩვენე მხოლოდ საბოლოო პასუხი ქართულად.
""".strip()

REVIEW_PROMPT = """
შენ ხარ ქართული ტექსტის რედაქტორი.
გაასწორე გრამატიკა და არაბუნებრივი გამოთქმები.
შეინარჩუნე საწყისი აზრი და ფაქტები.
არ დაამატო ახალი ინფორმაცია.
დააბრუნე მხოლოდ საბოლოო გამართული პასუხი.
""".strip()

MEMORY_PROMPT = """
შენ მართავ მომხმარებლის პირად მეხსიერებას.
შეამოწმე მომხმარებლის ბოლო შეტყობინება და შენახული ფაქტები.

თუ ახალი მნიშვნელოვანი ფაქტია, შესთავაზე add.
თუ ძველი ფაქტი აშკარად შეიცვალა, შესთავაზე update.
თუ დასამახსოვრებელი არაფერია, დააბრუნე ცარიელი სია.

არ გამოიტანო ვარაუდები.
არ შეინახო პაროლები, API გასაღებები ან მგრძნობიარე მონაცემები.
თუ ეჭვი გეპარება, არაფერი შეინახო.

დააბრუნე მხოლოდ JSON:
{"suggestions":[{"action":"add","id":null,"memory":"ფაქტი"}]}
თუ შეთავაზება არ არის საჭირო:
{"suggestions":[]}
""".strip()


# --------------------------------------------------
# თარიღი — თბილისის დროით
# --------------------------------------------------

def current_date_context():
    now = datetime.now(ZoneInfo("Asia/Tbilisi"))

    weekdays = [
        "ორშაბათი", "სამშაბათი", "ოთხშაბათი",
        "ხუთშაბათი", "პარასკევი", "შაბათი", "კვირა"
    ]

    months = [
        "იანვარი", "თებერვალი", "მარტი", "აპრილი",
        "მაისი", "ივნისი", "ივლისი", "აგვისტო",
        "სექტემბერი", "ოქტომბერი", "ნოემბერი", "დეკემბერი"
    ]

    return (
        f"დღევანდელი თარიღია {now.day} "
        f"{months[now.month - 1]} {now.year} წელი. "
        f"კვირის დღეა {weekdays[now.weekday()]}. "
        f"თბილისის დროა {now.strftime('%H:%M')}."
    )


# --------------------------------------------------
# Supabase — მეხსიერება
# --------------------------------------------------

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

    headers = {
        "apikey": key,
        "Content-Type": "application/json",
    }

    endpoint = f"{url}/rest/v1/nacarkekia_memory"
    query = {"owner_id": f"eq.{owner}"}

    if params:
        query.update(params)

    if method == "GET":
        response = requests.get(
            endpoint,
            headers=headers,
            params=query,
            timeout=15,
        )

    elif method == "POST":
        headers["Prefer"] = "return=minimal"
        response = requests.post(
            endpoint,
            headers=headers,
            params=query,
            json=payload,
            timeout=15,
        )

    elif method == "PATCH":
        headers["Prefer"] = "return=minimal"
        response = requests.patch(
            endpoint,
            headers=headers,
            params=query,
            json=payload,
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
        raise ValueError("უცნობი მოქმედება.")

    if not response.ok:
        raise RuntimeError(
            f"Supabase შეცდომა: HTTP {response.status_code}"
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


def update_memory(memory_id, value):
    return memory_request(
        "PATCH",
        params={"id": f"eq.{memory_id}"},
        payload={"memory": value},
    )


def delete_memory(memory_id):
    return memory_request(
        "DELETE",
        params={"id": f"eq.{memory_id}"},
    )


# --------------------------------------------------
# AI მოდელები
# --------------------------------------------------

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
        raise RuntimeError(
            f"HTTP {response.status_code}"
        )

    data = response.json()
    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError("მოდელმა პასუხი არ დააბრუნა.")

    choice = choices[0]
    message = choice.get("message") or {}
    answer = message.get("content")

    if isinstance(answer, list):
        answer = "\n".join(
            part.get("text", "")
            for part in answer
            if isinstance(part, dict) and part.get("text")
        )

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("მოდელმა ცარიელი პასუხი დააბრუნა.")

    return (
        answer.strip(),
        data.get("model", model_name),
        choice.get("finish_reason"),
    )


def ask_models(api_key, messages):
    errors = []

    for model_name in MODEL_ORDER:
        try:
            answer, actual_model, finish_reason = call_model(
                api_key,
                model_name,
                messages,
            )

            return answer, actual_model, finish_reason, errors

        except Exception as error:
            errors.append(
                f"{model_name}: {str(error)[:200]}"
            )

    return None, None, None, errors


# --------------------------------------------------
# მეხსიერების შეთავაზებები
# --------------------------------------------------

def suggest_memory_actions(
    api_key,
    model_name,
    user_text,
    existing_memories,
):
    memory_list = [
        {
            "id": item["id"],
            "memory": item["memory"],
        }
        for item in existing_memories
    ]

    messages = [
        {
            "role": "system",
            "content": MEMORY_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"მომხმარებლის ბოლო შეტყობინება:\n{user_text}\n\n"
                f"შენახული ფაქტები:\n"
                f"{json.dumps(memory_list, ensure_ascii=False)}"
            ),
        },
    ]

    result, _, _ = call_model(
        api_key,
        model_name,
        messages,
        max_tokens=400,
    )

    start = result.find("{")
    end = result.rfind("}")

    if start < 0 or end <= start:
        return []

    try:
        data = json.loads(result[start:end + 1])
    except json.JSONDecodeError:
        return []

    suggestions = data.get("suggestions", [])

    if not isinstance(suggestions, list):
        return []

    existing_by_id = {
        item["id"]: item["memory"]
        for item in existing_memories
    }

    existing_texts = {
        item["memory"].strip().casefold()
        for item in existing_memories
    }

    clean = []

    for item in suggestions[:2]:
        if not isinstance(item, dict):
            continue

        action = item.get("action")
        memory = item.get("memory")

        if action not in ("add", "update"):
            continue

        if not isinstance(memory, str):
            continue

        memory = memory.strip()

        if not memory or len(memory) > 250:
            continue

        if memory.casefold() in existing_texts:
            continue

        if action == "add":
            clean.append({
                "action": "add",
                "id": None,
                "memory": memory,
            })

        elif action == "update":
            memory_id = item.get("id")

            if memory_id not in existing_by_id:
                continue

            clean.append({
                "action": "update",
                "id": memory_id,
                "memory": memory,
                "old_memory": existing_by_id[memory_id],
            })

    return clean


# --------------------------------------------------
# Streamlit სესია
# --------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_memories" not in st.session_state:
    st.session_state.pending_memories = []

if "memory_notice" not in st.session_state:
    st.session_state.memory_notice = ""


# --------------------------------------------------
# გვერდითი პანელი — მეხსიერება
# --------------------------------------------------

st.sidebar.header("🧠 ნაცარქექიას მეხსიერება")
st.sidebar.caption("შენ აკონტროლებ შენახულ ინფორმაციას.")

manual_memory = st.sidebar.text_area(
    "ახალი ინფორმაციის დამატება",
    placeholder="მაგალითად: ჩემი საყვარელი თამაშია PUBG.",
)

if st.sidebar.button("დამატება", key="manual_add"):
    if manual_memory.strip():
        try:
            current = get_memories()

            duplicate = any(
                item["memory"].strip().casefold()
                == manual_memory.strip().casefold()
                for item in current
            )

            if duplicate:
                st.sidebar.info(
                    "ეს ინფორმაცია უკვე შენახულია."
                )
            else:
                save_memory(manual_memory.strip())
                st.sidebar.success(
                    "ინფორმაცია შენახულია."
                )
                st.rerun()

        except Exception as error:
            st.sidebar.error(str(error))

    else:
        st.sidebar.warning("ჯერ ჩაწერე ინფორმაცია.")


try:
    memories = get_memories()
    memory_ready = True

except Exception:
    memories = []
    memory_ready = False
    st.sidebar.error(
        "მეხსიერების ბაზასთან კავშირი ვერ შედგა."
    )


st.sidebar.subheader("შენახული ჩანაწერები")

if memory_ready and memories:
    for item in memories:
        with st.sidebar.expander(item["memory"][:55]):
            edited_value = st.text_area(
                "ჩანაწერი",
                value=item["memory"],
                key=f"edit_text_{item['id']}",
            )

            if st.button(
                "ცვლილების შენახვა",
                key=f"edit_save_{item['id']}",
                use_container_width=True,
            ):
                if edited_value.strip():
                    try:
                        update_memory(
                            item["id"],
                            edited_value.strip(),
                        )
                        st.rerun()

                    except Exception as error:
                        st.sidebar.error(str(error))

                else:
                    st.sidebar.warning(
                        "ცარიელი ჩანაწერის შენახვა არ შეიძლება."
                    )

            if st.button(
                "წაშლა",
                key=f"delete_{item['id']}",
                use_container_width=True,
            ):
                try:
                    delete_memory(item["id"])
                    st.rerun()

                except Exception as error:
                    st.sidebar.error(str(error))

elif memory_ready:
    st.sidebar.caption("მეხსიერება ჯერ ცარიელია.")


# --------------------------------------------------
# მეხსიერების შეთავაზებების დადასტურება
# --------------------------------------------------

if st.session_state.memory_notice:
    st.success(st.session_state.memory_notice)
    st.session_state.memory_notice = ""

if st.session_state.pending_memories:
    st.subheader("🧠 მეხსიერების შემოთავაზებები")

    st.write(
        "ნაცარქექიამ ეს ინფორმაცია ამოიცნო. "
        "შენ გადაწყვიტე, შევინახოთ თუ განვაახლოთ."
    )

    for index, candidate in enumerate(
        st.session_state.pending_memories
    ):
        if candidate["action"] == "update":
            st.caption(
                f"ძველი: {candidate['old_memory']}"
            )
            st.write(
                f"ახალი: {candidate['memory']}"
            )
        else:
            st.write(candidate["memory"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "დადასტურება",
                key=f"approve_{index}",
                use_container_width=True,
            ):
                try:
                    if candidate["action"] == "add":
                        save_memory(candidate["memory"])
                        notice = (
                            "ახალი ინფორმაცია დავიმახსოვრე."
                        )
                    else:
                        update_memory(
                            candidate["id"],
                            candidate["memory"],
                        )
                        notice = "ძველი ჩანაწერი განვაახლე."

                    st.session_state.pending_memories.pop(index)
                    st.session_state.memory_notice = notice
                    st.rerun()

                except Exception as error:
                    st.error(str(error))

        with col2:
            if st.button(
                "უარი",
                key=f"reject_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_memories.pop(index)
                st.rerun()

    if st.button("ყველა შეთავაზებაზე უარი"):
        st.session_state.pending_memories = []
        st.rerun()


# --------------------------------------------------
# ჩატი
# --------------------------------------------------

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
                    "organic_results",
                    [],
                )

                for item in results[:5]:
                    search_context += (
                        f"\nსათაური: {item.get('title', '')}\n"
                        f"აღწერა: {item.get('snippet', '')}\n"
                    )

            except Exception:
                st.warning(
                    "ინტერნეტძიება ვერ შესრულდა."
                )

        elif use_search and not search_key:
            st.warning(
                "SerpApi-ის გასაღები ვერ მოიძებნა."
            )

        # მიმდინარე თარიღი
        date_context = current_date_context()

        # მეხსიერება
        memory_context = "\n".join(
            f"- {item['memory']}"
            for item in memories
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        if memory_context:
            messages.append({
                "role": "system",
                "content": (
                    "ეს არის მომხმარებლის მიერ შენახული ინფორმაცია. "
                    "გამოიყენე მხოლოდ მაშინ, როცა კითხვას ეხება:\n"
                    + memory_context
                ),
            })

        messages.extend(
            st.session_state.chat_history[-8:]
        )

        user_message = (
            f"{date_context}\n\n"
            f"მომხმარებლის კითხვა:\n{question}\n\n"
            f"ინტერნეტში მოძიებული ინფორმაცია:\n"
            f"{search_context}\n\n"
            "თუ კითხვა თარიღს ეხება, დაეყრდენი მოცემულ "
            "მიმდინარე თარიღს. "
            "თუ ინტერნეტში მოძიებული ინფორმაცია არსებობს, "
            "გამოიყენე ის შესაბამისი კითხვებისთვის. "
            "არ მოიგონო ფაქტები ან წყაროები. "
            "მიპასუხე გამართული, ბუნებრივი ქართულით."
        )

        messages.append({
            "role": "user",
            "content": user_message,
        })

        # AI პასუხი
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

                except Exception:
                    pass

        # პასუხის ჩვენება
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

        # მეხსიერების მოქმედებების შეთავაზება
        if memory_ready:
            try:
                suggestions = suggest_memory_actions(
                    ai_key,
                    used_model,
                    question,
                    memories,
                )

                if suggestions:
                    st.session_state.pending_memories = suggestions

            except Exception:
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
                    st.markdown(f"- [{title}]({link})")

    if st.session_state.pending_memories:
        st.rerun()
