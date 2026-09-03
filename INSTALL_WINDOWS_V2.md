# BilimBellashuv Bot — Windows’da ishga tushirish

Bu ko‘rsatma faqat **final paket** uchun. Botni o‘rnatishdan oldin ZIP faylning nomi va ichidagi `bot_v2.py` hamda `miniapp` papkasi borligini tekshiring. Tokenni hech qachon chatga, rasmga yoki ZIP ichiga yozmang.

## 1. ZIP faylni ochish

ZIP faylni o‘ng tugma bilan bosing va **Extract All…** ni tanlang. Masalan, `C:\BilimBellashuvBot` papkasini tanlang. ZIP ichidagi fayllarni alohida-alohida ochib ko‘chirmang.

## 2. Tokenni kiritish

Papkadagi `.env.example` faylidan nusxa oling, nusxaning nomini aynan `.env` qiling. `.env` faylini Notepad bilan oching va quyidagilarni to‘ldiring:

```env
BOT_TOKEN=BotFather_bergan_token
V2_DB_PATH=bilimbellashuv_v2.sqlite3
MINI_APP_URL=https://sizning-https-manzilingiz
```

`BOT_TOKEN` qatoridan keyin BotFather bergan uzun token yoziladi. Tokenni boshqa odamga yubormang. `MINI_APP_URL` uchun oddiy `http://localhost` ishlamaydi; Telegram ichidagi Mini App telefonlarda ochilishi uchun HTTPS manzil kerak.

## 3. Kutubxonalarni o‘rnatish

Loyiha papkasini oching. Yuqoridagi manzil qatorini bosing, `cmd` deb yozing va Enter bosing. Qora oynada quyidagi buyruqni kiriting:

```bat
py -m pip install -r requirements-v2.txt
```

Bu buyruq birinchi marta internet orqali kerakli yordamchi dasturlarni o‘rnatadi.

## 4. Mini App serverini ishga tushirish

Agar HTTPS manzilingiz alohida joylashtirilgan bo‘lsa, Mini App serveri o‘sha manzilda ishlashi kerak. Oddiy kompyuterda sinash uchun quyidagini ishlatish mumkin, lekin bu manzil Telegram telefonida to‘g‘ridan-to‘g‘ri ishlamaydi:

```bat
py mini_server.py
```

Sifatli doimiy ishlash uchun Mini App va botni kompyuter o‘chsa ham ishlatib turadigan internetdagi joyga joylashtirish kerak. Bu joy “botning doim internetda ishlashi” uchun kerak bo‘ladi.

## 5. Botni ishga tushirish

Eng oson usul: loyiha papkasidagi `run_bot.bat` faylini ikki marta bosing. Agar Windows ogohlantirsa, **More info → Run anyway** ni tanlang.

Yoki aynan loyiha papkasidagi qora oynada:

```bat
py bot_v2.py
```

Bot ishlayotgan paytda shu qora oyna yopilmasin. Botni to‘xtatish uchun `Ctrl+C` bosing. Kompyuter o‘chsa yoki internet uzilsa, mahalliy bot ham vaqtincha ishlamaydi.

## 6. Birinchi tekshiruv

Telegram’da botga `/start` yuboring. Tilni tanlang, keyin **Test yaratish** tugmasini bosing. HTTPS Mini App manzili to‘g‘ri bo‘lsa, test yaratish oynasi ochiladi. Yaratilgan testning kodini boshqa Telegram hisobidan `/join KOD` orqali tekshiring.

## 7. Muhim eslatma

Mahalliy Windows usuli qo‘shimcha to‘lovsiz bo‘lishi mumkin, ammo kompyuter doim yoqilgan bo‘lishi shart. Kompyuter uzoq vaqt yoqilmaydigan bo‘lsa, botni internetdagi doimiy xizmatga joylashtirish kerak. Bu tanlovni final paket real Telegram’da tekshirilgandan keyin qilish ma’qul.
