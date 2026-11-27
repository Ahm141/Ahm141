import os, sqlite3, datetime as dt
from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool

DB = "secretary.db"
IRAQ = dt.timezone(dt.timedelta(hours=3))


# ---------- Memory DB (SQLite) ----------
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, date TEXT, time TEXT, notes TEXT DEFAULT '',
        status TEXT DEFAULT 'active');
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session TEXT, role TEXT, content TEXT);
    """)


# ---------- Tools ----------
@tool
def add_appointment(title: str, date: str, time: str, notes: str = "") -> str:
    """سجّل موعد جديد. date بصيغة YYYY-MM-DD و time بصيغة 24 ساعة HH:MM."""
    with db() as c:
        clash = c.execute(
            "SELECT title FROM appointments WHERE date=? AND time=? AND status='active'",
            (date, time)).fetchone()
        if clash:
            return f"تعارض: عندك موعد '{clash['title']}' بنفس الوقت. ما انسجل شي."
        cur = c.execute(
            "INSERT INTO appointments(title,date,time,notes) VALUES(?,?,?,?)",
            (title, date, time, notes))
        return f"تم تسجيل الموعد رقم {cur.lastrowid}: {title} يوم {date} الساعة {time}"

@tool
def list_appointments(date: str = "") -> str:
    """اعرض المواعيد الفعالة. اترك date فارغ لعرض كل المواعيد القادمة."""
    with db() as c:
        if date:
            rows = c.execute("SELECT * FROM appointments WHERE date=? AND status='active' ORDER BY time", (date,)).fetchall()
        else:
            today = dt.datetime.now(IRAQ).strftime("%Y-%m-%d")
            rows = c.execute("SELECT * FROM appointments WHERE date>=? AND status='active' ORDER BY date,time", (today,)).fetchall()
    if not rows:
        return "ماكو مواعيد."
    return "\n".join(f"#{r['id']} | {r['date']} {r['time']} | {r['title']} {r['notes']}" for r in rows)

@tool
def cancel_appointment(appointment_id: int) -> str:
    """الغِ موعد حسب رقمه."""
    with db() as c:
        cur = c.execute("UPDATE appointments SET status='cancelled' WHERE id=? AND status='active'", (appointment_id,))
        return "انلغى الموعد." if cur.rowcount else "ماكو موعد فعال بهذا الرقم."

TOOLS = [add_appointment, list_appointments, cancel_appointment]



def system_prompt() -> str:
    now = dt.datetime.now(IRAQ)
    days = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
    return f"""انتِ "نور"، سكرتيرة احمد الشخصية، وتحجين وياه صوت بصوت مثل صديقة شغلها تنظيم وقته.
الأسلوب: عراقي عفوي وطبيعي، جملة او جملتين بس. استعملي حجي الناس اليومي مثل: هلا، اي، زين، تمام، ابشر، شلون، شنو، هسه، اكيد. لا تبدين كل رد بنفس الكلمة. اذا الجو يسمح ممكن مزحة خفيفة.
ردك يتحول لصوت، فلا تستعملين رموز ولا نقاط ولا ترقيم ولا ايموجي ولا اقواس، وتكتبين الساعات والارقام بالكلمات (الساعة خمسة ونص). اذا عنده اكثر من ثلاث مواعيد اذكري اول ثلاثة وسأليه اذا يريد البقية.
الوقت الحالي: {days[now.weekday()]} {now:%Y-%m-%d} الساعة {now:%H:%M} بتوقيت العراق.
القواعد:
- بالأدوات استعملي الصيغة الرقمية (YYYY-MM-DD و HH:MM)، وبكلامك استعملي الكلمات.
- حوّلي "باجر" و"بعد باجر" و"الخميس الجاي" الى تاريخ حقيقي حسب الوقت الحالي.
- اذا ينقص عنوان الموعد او وقته، اسألي سؤال واحد قصير. لا تخمنين.
- لا تقولين سجلت او الغيت الا بعد ما الأداة ترجع نجاح.
- اذا الكلام غير واضح (صوت مقطوع)، اطلبي منه يعيد بلطف."""

def history(session: str, n: int = 12):
    with db() as c:
        rows = c.execute("SELECT role,content FROM messages WHERE session=? ORDER BY id DESC LIMIT ?", (session, n)).fetchall()
    return [(r["role"], r["content"]) for r in reversed(rows)]


def save(session: str, role: str, content: str):
    with db() as c:
        c.execute("INSERT INTO messages(session,role,content) VALUES(?,?,?)", (session, role, content))
