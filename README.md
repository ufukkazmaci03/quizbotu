# Quiz Discord Bot (Python)

Basit bir Discord bilgi yarışması botu. Slash komutlarıyla kişisel quiz oturumu başlatır, soru sorar ve skor tutar.

## Dosya yapısı

```text
quizbotu/
├─ bot/
│  ├─ main.py
│  └─ quiz_manager.py
├─ data/
│  └─ questions.json
├─ .env.example
├─ requirements.txt
└─ README.md
```

## Kurulum

1. Python 3.11+ önerilir.
2. Bağımlılıkları kur:

```bash
pip install -r requirements.txt
```

3. `.env.example` dosyasını `.env` olarak kopyala ve token bilgini yaz:

```bash
cp .env.example .env
```

4. Botu çalıştır:

```bash
python bot/main.py
```

## Komutlar

- `/quiz-start` → Yeni quiz başlatır.
- `/quiz-next` → Sıradaki soruyu gönderir.
- `/quiz-score` → Mevcut skoru gösterir.
- `/quiz-stop` → Oyunu sonlandırır.

## Notlar

- Sorular `data/questions.json` içinden yüklenir.
- Her kullanıcı kendi ayrı oturumuna sahiptir.
- Varsayılan prefix tanımlı olsa da bu örnek slash komutları kullanır.
