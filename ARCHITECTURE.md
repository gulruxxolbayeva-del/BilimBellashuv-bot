# BilimBellashuv Bot — qayta yoziladigan arxitektura

## Maqsad

Bot uchta test turini boshqaradi: faqat umumiy quiz, faqat umumiy yozma test va umumiy quiz + yozma test. Har bir test savollar banki, sessiyalar, PDF eksporti, diplomlar, natijalar, tahrirlash va bekor qilish bilan alohida boshqariladi.

## Asosiy qismlar

| Qism | Vazifasi |
|---|---|
| Telegram bot yadrosi | `/start`, menyular, kod orqali kirish, xabarnomalar va natijalarni boshqaradi |
| Telegram Mini App | Test sozlamalari, savol/rasm/variant/ball kiritish va yozma javob formasini ko‘rsatadi |
| SQLite ma’lumotlar bazasi | Savollar banki, sessiyalar, ishtirokchilar, javoblar, PDF va diplom holatini saqlaydi |
| Sessiya menejeri | Umumiy musobaqa, yakka test va quiz+yozma bosqichlarining vaqtini boshqaradi |
| PDF generator | Quiz, yozma test, javoblar kaliti va diplom PDF’larini yaratadi |
| Baholash qismi | Quiz javoblarini aniq, yozma javoblarni esa normalizatsiya va mazmuniy baholash orqali tekshiradi |
| Til katalogi | 20 ta interfeys tilidagi menyu va tizim xabarlarini saqlaydi |

## Test yaratish oqimi

Yaratuvchi `Test yaratish` menyusidan test turini tanlaydi. Mini App ochilib, test nomi, savollar soni, vaqt rejimi, vaqt mintaqasi, boshlanish sanasi-vaqti, ballar, aralashtirish, PDF, natijalar va diplom sozlamalari kiritiladi. Quiz savolida variantlar va to‘g‘ri variant; yozma savolida qabul qilinadigan javob mezoni va javob namunalarini kiritish mumkin. Har bir savolga rasm biriktiriladi.

## Sessiya qoidalari

Umumiy sessiya faol kod bilan yaratiladi. Kod faol sessiyalar orasida takrorlanmaydi; sessiya tugagach yoki bekor qilingach faolsizlanadi. Yangi ishga tushirish eski bankni o‘zgartirmasdan yangi sessiya yaratadi. Quiz+yozma sessiyada quiz natijasi oraliqda yashiriladi, yozma qism 10 soniyalik sanashdan keyin boshlanadi va umumiy natija oxirida ko‘rsatiladi.

Yakka test uchun doimiy alohida kod saqlanadi. Kod kiritilganda test darhol boshlanadi. Urinishlar ko‘rsatiladi, rasmiy saqlanadigan ko‘rsatkich esa faqat eng yaxshi natijadir.

## Xavfsizlik

`BOT_TOKEN` faqat `.env` yoki hosting secrets orqali olinadi. Mini App ma’lumotlari bot tomonidan foydalanuvchi identifikatori bilan tekshiriladi. Test, tahrirlash, o‘chirish, bekor qilish va natijalarni ochish huquqlari faqat yaratuvchiga beriladi.

## Muhim texnik eslatma

Telegram Mini App ishlashi uchun Mini App fayllari internetda HTTPS manzil orqali ochilishi kerak. Windows’dagi mahalliy ishga tushirish bot yadrosini sinash uchun yetarli, lekin Mini App’ni Telegram ichida to‘liq ochish va botni 24/7 ishlatish uchun keyin HTTPS hosting kerak bo‘ladi.
