
import json
import time
import re
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
შეინარჩუნე საწყისი აზრი, რიცხვები და ფაქტები.
არ დაამატო ახალი ინფორმაცია.
დააბრუნე მხოლოდ საბოლოო გამართული პასუხი.
""".strip()

MEMORY_PROMPT = """
შეამოწმე მომხმარებლის ბოლო შეტყობინება და შენახული ფაქტები.
თუ ახალი მნიშვნელოვანი ფაქტია, შესთავაზე add.
თუ ძველი ფაქტი აშკარად შეიცვალა, შესთავაზე update.
თუ დასამახსოვრებელი არაფერია, დააბრუნე ცარიელი სია.
არ გამოიტანო ვარაუდები. არ შეინახო პაროლები ან გასაღებები.
დააბრუნე მხოლოდ JSON:
{"suggestions":[{"action":"add","id":null,"memory":"ფაქტი"}]}
""".strip()


# --------------------------------------------------
# თარიღი
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
# ამინდი — Open-Meteo
# --------------------------------------------------

CITIES = {
    "თბილისი": (41.7151, 44.8271),
    "ბათუმი": (41.6168, 41.6367),
    "ქუთაისი": (42.2679, 42.6946),
    "რუსთავი": (41.5495, 44.9932),
    "გორი": (41.9842, 44.1158),
    "ზუგდიდი": (42.5088, 41.8709),
    "თელავი": (41.9198, 45.4732),
    "ფოთი": (42.1462, 41.6719),
    "ახალციხე": (41.6390, 42.9826),
    "ბორჯომი": (41.8417, 43.3792),
    "მესტია": (43.0458, 42.7278),
    "ოზურგეთი": (41.9244, 42.0068),
    "სენაკი": (42.2697, 42.0676),
    "ქობულეთი": (41.8236, 41.7753),
}

WEATHER_WORDS = [
    "ამინდ", "ტემპერატურ", "წვიმ", "თოვლ",
    "ქარ", "პროგნოზ", "weather", "temperature",
    "forecast", "rain", "snow"
]

WEATHER_CODES = {
    0: "მოწმენდილი ცა",
    1: "უმეტესად მზიანი",
    2: "ნაწილობრივ ღრუბლიანი",
    3: "მოღრუბლული",
    45: "ნისლი",
    48: "ნისლი",
    51: "მსუბუქი ჟინჟღლი",
    53: "ჟინჟღლი",
    55: "ძლიერი ჟინჟღლი",
    61: "მსუბუქი წვიმა",
    63: "წვიმა",
    65: "ძლიერი წვიმა",
    71: "მსუბუქი თოვლი",
    73: "თოვლი",
    75: "ძლიერი თოვლი",
    80: "წვიმის შხაპუნა",
    81: "წვიმა",
    82: "ძლიერი წვიმა",
    95: "ჭექა-ქუხილი",
    96: "სეტყვიანი ჭექა-ქუხილი",
    99: "ძლიერი სეტყვა და ჭექა-ქუხილი",
}


def find_city(question):
    text = question.casefold()

    # ქალაქების სახელების ამოცნობა
    aliases = {
        "თბილისი": ["თბილისი", "tbilisi", "ტბილისი"],
        "ბათუმი": ["ბათუმი", "batumi"],
        "ქუთაისი": ["ქუთაისი", "kutaisi"],
        "რუსთავი": ["რუსთავი", "rustavi"],
        "გორი": ["გორი", "gori"],
        "ზუგდიდი": ["ზუგდიდი", "zugdidi"],
        "თელავი": ["თელავი", "telavi"],
        "ფოთი": ["ფოთი", "poti"],
        "ახალციხე": ["ახალციხე", "akhaltsikhe"],
        "ბორჯომი": ["ბორჯომი", "borjomi"],
        "მესტია": ["მესტია", "mestia"],
        "ოზურგეთი": ["ოზურგეთი", "ozurgeti"],
        "სენაკი": ["სენაკი", "senaki"],
        "ქობულეთი": ["ქობულეთი", "kobuleti"],
    }

    for city, names in aliases.items():
        for name in names:
            if name in text:
                return city

    # თუ ქალაქი არ არის მითითებული, ნაგულისხმევად თბილისი
    # გამოიყენება მხოლოდ ზოგადი კითხვისთვის.
    general_phrases = [
        "ამინდი როგორი", "როგორი ამინდია",
        "დღეს როგორი ამინდია", "ამინდი მაინტერესებს",
        "weather now", "weather today"
    ]

    if any(phrase in text for phrase in general_phrases):
        return "თბილისი"

    return None


def get_weather_context(question):
    lowered = question.casefold()

    if not any(word in lowered for word in WEATHER_WORDS):
        return ""

    city = find_city(question)

    if not city:
        return (
            "ამინდის მოთხოვნა ამოცნობილია, მაგრამ ქალაქის სახელი "
            "ვერ განისაზღვრა. სხვა ქალაქის მონაცემი არ გამოიყენო. "
            "სთხოვე მომხმარებელს, მიუთითოს ქალაქი."
        )

    latitude, longitude = CITIES[city]

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "hourly": (
                    "temperature_2m,precipitation_probability,"
                    "weather_code"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                ),
                "timezone": "Asia/Tbilisi",
                "forecast_days": 7,
            },
            timeout=(4, 10),
        )

        response.raise_for_status()
        data = response.json()

        current = data.get("current")
        hourly = data.get("hourly")
        daily = data.get("daily")

        if not current or not daily:
            return (
                f"{city}-ისთვის ამინდის მონაცემები სრულად "
                "არ დაბრუნებულა. სხვა ქალაქის მონაცემი არ გამოიყენო."
            )

        code = current.get("weather_code")
        description = WEATHER_CODES.get(code, "მდგომარეობა უცნობია")

        lines = [
            f"ამინდის მონაცემები კონკრეტულად ქალაქისთვის: {city}.",
            f"ახლანდელი ტემპერატურა: {current.get('temperature_2m')}°C.",
            f"შეგრძნებით: {current.get('apparent_temperature')}°C.",
            f"მდგომარეობა: {description}.",
            f"ტენიანობა: {current.get('relative_humidity_2m')}%.",
            f"ქარის სიჩქარე: {current.get('wind_speed_10m')} კმ/სთ.",
            f"ნალექი ამჟამად: {current.get('precipitation')} მმ.",
            "",
            "დღევანდელი და მომდევნო დღეების პროგნოზი:"
        ]

        dates = daily.get("time", [])
        minimums = daily.get("temperature_2m_min", [])
        maximums = daily.get("temperature_2m_max", [])
        rain_probs = daily.get("precipitation_probability_max", [])
        codes = daily.get("weather_code", [])

        for i, date in enumerate(dates):
            day_code = codes[i] if i < len(codes) else None
            day_description = WEATHER_CODES.get(
                day_code, "მდგომარეობა უცნობია"
            )

            low = minimums[i] if i < len(minimums) else "უცნობია"
            high = maximums[i] if i < len(maximums) else "უცნობია"
            rain = rain_probs[i] if i < len(rain_probs) else "უცნობია"

            lines.append(
                f"{date}: {day_description}; "
                f"მინიმუმი {low}°C; მაქსიმუმი {high}°C; "
                f"ნალექის ალბათობა {rain}%."
            )

        # დღევანდელი საათობრივი პროგნოზის მოკლე ნაწილი
        if hourly:
            lines.append("")
            lines.append("საათობრივი პროგნოზი:")

            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            probabilities = hourly.get(
                "precipitation_probability", []
            )

            today = datetime.now(ZoneInfo("Asia/Tbilisi")).date().isoformat()
            count = 0

            for i, timestamp in enumerate(times):
                if not timestamp.startswith(today):
                    continue

                if i >= len(temps):
                    continue

                rain = (
                    probabilities[i]
                    if i < len(probabilities)
                    else "უცნობია"
                )

                lines.append(
                    f"{timestamp[-5:]} — {temps[i]}°C, "
                    f"ნალექის ალბათობა {rain}%."
                )

                count += 1
                if count >= 8:
                    break

        lines.append("")
        lines.append("წყარო: Open-Meteo.")
        lines.append(
            "ეს მონაცემები მხოლოდ ზემოთ მითითებულ ქალაქს ეკუთვნის."
        )

        return "\n".join(lines)

    except (
        requests.exceptions.RequestException,
        ValueError,
        KeyError,
        TypeError,
    ):
        return (
            f"{city}-ისთვის ამინდის სერვისთან კავშირი ვერ შედგა. "
            "არ გამოიყენო სხვა ქალაქის ამინდის მონაცემები. "
            "უთხარი მომხმარებელს, რომ პროგნოზი დროებით მიუწვდომელია."
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
        raise RuntimeError("Supabase-ის Secrets სრულად შევსებული არ არის.")

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
            endpoint, headers=headers, params=query, timeout=15
        )
    elif method == "POST":
        headers["Prefer"] = "return=minimal"
        response = requests.post(
            endpoint, headers=headers, params=query,
            json=payload, timeout=15
        )
    elif method == "PATCH":
        headers["Prefer"] = "return=minimal"
        response = requests.patch(
            endpoint, headers=headers, params=query,
            json=payload, timeout=15
        )
    elif method == "DELETE":
        response = requests.delete(
            endpoint, headers=headers, params=query, timeout=15
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
        payload={"owner_id": owner, "memory": value},
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
        raise RuntimeError(f"HTTP {response.status_code}")

    data = response.json()
    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError("მოდელმა პასუხი არ დააბრუნა.")

    message = choices[0].get("message") or {}
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
        choices[0].get("finish_reason"),
    )


def ask_models(api_key, messages):
    errors = []

    for model_name in MODEL_ORDER:
        try:
            answer, actual_model, finish_reason = call_model(
                api_key, model_name, messages
            )
            return answer, actual_model, finish_reason, errors
        except Exception as error:
            errors.append(f"{model_name}: {str(error)[:200]}")

    return None, None, None, errors


# --------------------------------------------------
# მეხსიერების შეთავაზებები
# --------------------------------------------------

def suggest_memory_actions(api_key, model_name, user_text, existing):
    memory_list = [
        {"id": item["id"], "memory": item["memory"]}
        for item in existing
    ]

    messages = [
        {"role": "system", "content": MEMORY_PROMPT},
        {
            "role": "user",
            "content": (
                f"მომხმარებლის შეტყობინება:\n{user_text}\n\n"
                f"შენახული ფაქტები:\n"
                f"{json.dumps(memory_list, ensure_ascii=False)}"
            ),
        },
    ]

    result, _, _ = call_model(
        api_key, model_name, messages, max_tokens=400
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

    existing_texts = {
        item["memory"].strip().casefold()
        for item in existing
    }

    existing_by_id = {
        item["id"]: item["memory"]
        for item in existing
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
# გვერდითი პანელი
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
                st.sidebar.info("ეს ინფორმაცია უკვე შენახულია.")
            else:
                save_memory(manual_memory.strip())
                st.sidebar.success("ინფორმაცია შენახულია.")
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
    st.sidebar.error("მეხსიერების ბაზასთან კავშირი ვერ შედგა.")


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
                        update_memory(item["id"], edited_value.strip())
                        st.rerun()
                    except Exception as error:
                        st.sidebar.error(str(error))

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

    for index, candidate in enumerate(
        st.session_state.pending_memories
    ):
        if candidate["action"] == "update":
            st.caption(f"ძველი: {candidate['old_memory']}")
            st.write(f"ახალი: {candidate['memory']}")
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
                        notice = "ახალი ინფორმაცია დავიმახსოვრე."
                    else:
                        update_memory(
                            candidate["id"], candidate["memory"]
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
        st.error("OpenRouter-ის გასაღები ვერ მოიძებნა.")
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

            except Exception:
                st.warning("ინტერნეტძიება ვერ შესრულდა.")

        elif use_search and not search_key:
            st.warning("SerpApi-ის გასაღები ვერ მოიძებნა.")

        date_context = current_date_context()
        weather_context = get_weather_context(question)

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
                    "მომხმარებლის შენახული ინფორმაცია. "
                    "გამოიყენე მხოლოდ შესაბამის კითხვაზე:\n"
                    + memory_context
                ),
            })

        messages.extend(st.session_state.chat_history[-8:])

        user_message = (
            f"{date_context}\n\n"
            f"მომხმარებლის კითხვა:\n{question}\n\n"
            f"ამინდის მონაცემები:\n{weather_context}\n\n"
            f"ინტერნეტში მოძიებული ინფორმაცია:\n{search_context}\n\n"
            "მნიშვნელოვანი წესები:\n"
            "თუ ამინდის მონაცემებში კონკრეტული ქალაქია მითითებული, "
            "პასუხი მხოლოდ იმ ქალაქს უნდა ეხებოდეს. "
            "არასოდეს ჩაანაცვლო ერთი ქალაქი მეორით. "
            "თუ ამინდის მონაცემი მიუწვდომელია, პირდაპირ თქვი ეს. "
            "არ გამოიგონო ტემპერატურა, ქარი ან ნალექი. "
            "თუ ქალაქი ვერ ამოიცანი, სთხოვე მომხმარებელს დაზუსტება. "
            "თარიღზე პასუხისას გამოიყენე მოცემული მიმდინარე თარიღი. "
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
            st.error("უფასო მოდელები ამჟამად მიუწვდომელია.")
            for error in errors:
                st.code(error)
            st.stop()

        # ამინდის პასუხში რიცხვების შეცვლის თავიდან აცილება:
        # ამინდის პასუხს დამატებით AI რედაქტორს არ ვუგზავნით.
        is_weather_question = any(
            word in question.casefold()
            for word in WEATHER_WORDS
        )

        quality_checked = False

        if check_quality and not is_weather_question:
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

        st.subheader("ნაცარქექიას პასუხი")
        st.write(answer)

        if finish_reason == "length":
            st.warning("პასუხი შესაძლოა ბოლომდე არ დასრულებულა.")

        if quality_checked:
            st.caption("ქართული ტექსტი დამატებით შემოწმებულია.")

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

        # მეხსიერების შეთავაზება
        if memory_ready:
            try:
                suggestions = suggest_memory_actions(
                    ai_key, used_model, question, memories
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

        if results:
            st.subheader("გამოყენებული წყაროები")

            for item in results[:5]:
                title = item.get("title", "წყარო")
                link = item.get("link", "")

                if link:
                    st.markdown(f"- [{title}]({link})")

    if st.session_state.pending_memories:
        st.rerun()
