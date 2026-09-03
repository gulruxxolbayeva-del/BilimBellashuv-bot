# BilimBellashuv Bot

BilimBellashuv Bot — Telegram ichida test yaratish va ishlash uchun mo‘ljallangan ko‘p tilli bot. **G‘oya/Loyiha muallifi: Gulmira Norpulatova. Loyihalashtiruvchi: AI.** Kanal: https://t.me/FAKTastika1.

## Nimalar ishlaydi

Bot Telegram ichida alohida Mini App oynasida quiz, yozma, combined yoki doimiy kodli yakka test yaratadi. Savollar banki 2 000 tagacha savolni saqlaydi; bank o‘chirilmaydi va har bir qayta ishga tushirish alohida sessiya hisoblanadi. Quiz savollarida 2–4 variant, to‘g‘ri javob, ball va ixtiyoriy rasm beriladi. Yozma savolda qabul qilinadigan javoblar, tekshirish qoidalari, ball va rasm saqlanadi.

Umumiy testda qatnashuvchi kod bilan ro‘yxatdan o‘tadi va boshlanishdan oldingi 5 daqiqada tayyorligini tasdiqlaydi. Belgilangan vaqtda test birgalikda boshlanadi. Har bir javobdan keyin keyingi savol chiqadi; orqaga qaytish yo‘q. Vaqt tugasa qolgan savollar avtomatik javobsiz deb topshiriladi.

Combined testda quiz qismi tugagach oraliq natija ko‘rsatilmaydi. 10 soniyalik tayyorgarlikdan keyin yozma qism boshlanadi va oxirida quiz, yozma hamda umumiy natija ko‘rsatiladi. Yakka testning kodi doimiy bo‘ladi, kod kiritilishi bilan test darhol boshlanadi va ko‘p urinishlardan faqat eng yaxshi natija rasmiy natija sifatida ajratiladi.

Natijada to‘g‘ri, xato, javobsiz javoblar, foiz, tanlangan javoblar va to‘g‘ri javoblar ko‘rsatiladi. Yaratuvchi reyting, teng o‘rinlar, Telegram username mavjud bo‘lsa profil havolalari, PDF va CSV fayllarni oladi. Diplom mezonini yoqish, minimal foiz yoki ball belgilash va qo‘shimcha matn kiritish mumkin. Diplomda muallif va kanal havolasi yozilmaydi.

Interfeys quyidagi 20 tilni o‘z ichiga oladi: o‘zbek, rus, ingliz, xitoy, fransuz, koreys, yapon, qozoq, tojik, turk, arab, nemis, ispan, portugal, italyan, hind, urdu, bengal, indonez va vetnam. Yaratuvchi kiritgan savol va variantlar avtomatik tarjima qilinmaydi.

## Final entrypoint

Final botni ishga tushirish fayli — `bot_v2.py`. Eski `bot.py` faqat tarixiy namuna sifatida qoladi va final bot uchun ishlatilmaydi.

```bat
py -m pip install -r requirements-v2.txt
py bot_v2.py
```

Mini App serverining alohida ishga tushirish fayli — `mini_server.py`. Telegram telefon ilovasida Mini App ochilishi uchun `.env` ichidagi `MINI_APP_URL` HTTPS manzil bo‘lishi kerak.

## Muhit fayli

`.env.example` nusxasini `.env` deb nomlang:

```env
BOT_TOKEN=PASTE_BOTFATHER_TOKEN_HERE
V2_DB_PATH=bilimbellashuv_v2.sqlite3
MINI_APP_URL=https://sizning-https-manzilingiz
```

Token maxfiy hisoblanadi. Uni chatga yubormang va ZIP ichiga qo‘shmang.

## Doim internetda ishlashi

Windows kompyuterda ishlatilganda bot faqat qora terminal oynasi va kompyuter yoqilganida ishlaydi. Kompyuter uzoq vaqt o‘chiq bo‘lsa, bot ham javob bermaydi. Botning doim internetda ishlashi uchun bot va Mini App’ni doimiy online xizmatga joylashtirish kerak.

Batafsil Windows ko‘rsatmasi `INSTALL_WINDOWS_V2.md` faylida berilgan.
