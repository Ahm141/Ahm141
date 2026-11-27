# سكرتيرة حبوشي (صوت LiveKit)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # املا المفاتيح

# ترمنال 1: السيرفر والواجهة
uvicorn app:app --reload
# ترمنال 2: وكيل الصوت (اول مرة ينزل نماذج VAD)
python agent.py download-files
python agent.py dev
```
افتح http://localhost:8000 واضغط "ابدأ الحديث".
http://127.0.0.1:8000/api/token
http://127.0.0.1:8000/
