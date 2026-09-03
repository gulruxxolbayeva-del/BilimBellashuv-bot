# BilimBellashuv Bot — yangilangan texnik spetsifikatsiya

**Loyiha muallifi:** Gulmira Norpulatova  
**Loyihalashtiruvchi:** AI  
**Kanal:** https://t.me/FAKTastika1

## Test turlari

Yaratuvchi test yaratishda uchta turdan birini tanlaydi: faqat umumiy quiz test, faqat umumiy yozma test yoki umumiy quiz + yozma test. Birinchi ikki tur mustaqil ishlaydi. Uchinchi tur bitta kodli ikki bosqichli sessiya bo‘lib, avval quiz, so‘ng 10 soniyalik tayyorgarlikdan keyin yozma qism boshlanadi.

Quiz + yozma sessiyada quiz qismi tugaganda oraliq natija qatnashchiga ko‘rsatilmaydi. Yozma qism tugagach quiz natijasi, yozma natija va umumiy natija birgalikda chiqariladi. Har bir qismning vaqt rejimi va davomiyligi alohida belgilanadi.

## Test yaratish sozlamalari

Yozma test yaratilayotganda yaratuvchi javobni tekshirish mezonlarini o‘zi belgilaydi. U katta-kichik harf, bo‘sh joy va tinish belgilariga munosabatni hamda bir nechta qabul qilinadigan javoblarni kiritish imkonini tanlaydi. Quiz va yozma testlarda har bir savolga standart ravishda 1 ball beriladi. Sozlamalar oynasining yuqorisida shu standart ko‘rsatiladi; yaratuvchi xohlasa har bir savol ballini o‘zgartiradi.

Quiz va yozma test savollarining har biriga rasm biriktirish mumkin. Rasm savol bilan birga ko‘rsatiladi va PDF eksportida ham saqlanadi.

## Test modeli

Test yaratuvchi savollar bankini bir marta yaratadi. Bank 2000 tagacha savolni saqlaydi va o‘chirilmaydi. Har bir ishga tushirish alohida sessiya sifatida yaratiladi; sessiyada beriladigan savollar soni, kod, boshlanish vaqti va vaqt rejimi alohida saqlanadi.

## Yakka test rejimi

Yakka test umumiy musobaqadan mustaqil ishlaydi. Unga alohida doimiy kod beriladi; shu kod orqali foydalanuvchi istalgan vaqtda va istalgancha testni qayta ishlashi mumkin. Kod kiritilgach test darhol boshlanadi. Yakka test sozlamalari alohida menyuda bo‘ladi: vaqt rejimi, savollarni aralashtirish, variantlarni aralashtirish, beriladigan savollar soni va boshqa parametrlarni yaratuvchi tanlaydi.

Har bir urinishda natija hisoblanadi va foydalanuvchiga ko‘rsatiladi, ammo rasmiy saqlanadigan natija faqat eng yaxshi natija bo‘ladi. Eng yaxshi natija eng ko‘p to‘g‘ri javob yoki teng bo‘lsa yuqoriroq foiz asosida aniqlanadi. Yakka test yakunida savollar, tanlangan javoblar va to‘g‘ri javoblar ko‘rsatiladi.

## Vaqt rejimi

Yaratuvchi ikki rejimdan birini tanlaydi: butun test uchun umumiy vaqt yoki har bir savol uchun alohida vaqt. Har bir savol rejimida vaqt tugasa, tanlanmagan savol javobsiz deb hisoblanadi va bot keyingi savolga o‘tadi. Har ikkala rejimda ham javob berilgach ortga qaytish mumkin emas.

## Test eksporti

QuizBot’ga eksport qilish funksiyasi qo‘shilmaydi. Yaratuvchi testni PDF fayl sifatida yoki botning o‘zida ishlanadigan test sifatida oladi. Bot formatidagi test umumiy musobaqa yoki doimiy kodli yakka test ko‘rinishida ishlatiladi.

## PDF eksporti

Yaratuvchi PDF yaratishda test turiga mos ko‘rinishni tanlaydi. Quiz PDF’da savollar va variantlar beriladi. Yozma test PDF’da savollar, javob yozish uchun bo‘sh joylar va kerak bo‘lsa javoblar kaliti bo‘ladi. Har ikkala test uchun yaratuvchi to‘g‘ri javoblarni savol ostida ko‘rsatish, alohida javoblar kaliti qilish yoki javoblarni yashirishni tanlaydi. Yaratuvchi PDF’ni faqat o‘ziga yoki shu sessiyada test ishlagan ishtirokchilarga yuborishi mumkin.

## Kodlar va sessiyalar

Umumiy musobaqa kodi boshqa faol test bilan takrorlanmaydi. Kod allaqachon band bo‘lsa, bot yangi kod kiritishni so‘raydi. Musobaqa tugagach kod faolsizlanadi. Test qayta ishga tushirilganda savollar banki saqlangan holda yangi sessiya va yangi faol kod yaratiladi.

## Diplomlar

Diplom PDF shaklida yuboriladi. Diplomda loyiha muallifi va kanal havolasi ko‘rsatilmaydi; unda ishtirokchi ismi, test nomi, natija va sana bo‘lishi mumkin.

## Natijalar

Yaratuvchi natijalarni ko‘radi, reytingni tekshiradi va keyin natijalarni barcha ishtirokchilarga ko‘rsatish yoki yashirishni tanlaydi. Ishtirokchi o‘z natijasi, xatolari, savollari va to‘g‘ri javoblarini ko‘rishi mumkin.

## Diplomlar

Yaratuvchi diplom yuborishni yoqadi yoki o‘chiradi, minimal foiz yoki ball mezonini belgilaydi va diplom dizaynidagi ism, test nomi, natija, sana hamda muallif ma’lumotlarini tasdiqlaydi. Mezonga javob bergan ishtirokchilarga diplom avtomatik yuboriladi.

## Tavsiya etiladigan ma’lumotlar jadvallari

| Jadval | Vazifasi |
|---|---|
| `quiz_banks` | Test nomi, yaratuvchi va 2000 tagacha savollar banki |
| `questions` | Savol matni, variantlar va to‘g‘ri javob |
| `sessions` | Qayta ishga tushirish, kod, vaqt, rejim va ko‘rinish sozlamalari |
| `participants` | Sessiya qatnashchilari va tayyorlik holati |
| `answers` | Har bir qatnashchining savol bo‘yicha javobi |
| `certificates` | Diplom berilganligi va mezon natijasi |

## Ko‘p tillilik

Bot interfeysi o‘zbek, rus, ingliz, xitoy, fransuz, koreys, yapon, qozoq, tojik, turk, arab, nemis, ispan, portugal, italyan, hind, urdu, bengal, indonez va vetnam tillarida bo‘ladi. Test yaratuvchisi kiritgan savol va variantlar avtomatik o‘zgartirilmaydi.

## Telegram Mini App

Quiz va yozma testlarni yaratish jarayoni Telegram ichida ochiladigan Mini App orqali bajariladi. Bot chatida savol, variant va sozlamalarni ketma-ket alohida xabarlar bilan so‘rash o‘rniga, yaratuvchi maxsus oynada test turini, test nomini, savollar sonini, vaqtni, ballarni, aralashtirishni, savol matnini, variantlarni, to‘g‘ri javobni, yozma javob mezonlarini va rasmni kiritadi. Saqlash tugmasi bosilganda ma’lumotlar avtomatik ravishda test bankiga yoziladi.

Yozma testni ishlash paytida ham ishtirokchi javobni Telegram ichidagi Mini App oynasiga matn sifatida kiritadi; javob oddiy bot chatida alohida xabar sifatida ko‘rinmaydi. Quiz testda savol va variantlar ham Mini App yoki bot ichidagi belgilangan test interfeysida ko‘rsatiladi, ortiqcha chat xabarlari chiqarilmaydi.

## Yozma baholash

Yozma javoblar avtomatik mazmuniy baholanadi. Katta-kichik harf, ortiqcha bo‘sh joy va oddiy tinish belgilari hisobga olinmaydi. Mazmuni bir xil bo‘lgan turli iboralar to‘g‘ri deb qabul qilinadi.

## Savol ballari va rasmlar

Har bir quiz va yozma savolga standart ravishda 1 ball beriladi. Yaratuvchi test sozlamalari vaqtida bu standartni ko‘radi va xohlasa ballarni o‘zgartiradi. Har bir savolga rasm biriktirish mumkin; rasm Mini App’da, test vaqtida va PDF eksportida ko‘rsatiladi.

## Test turlarining yakuniy menyusi

Yaratuvchi faqat umumiy quiz, faqat umumiy yozma yoki quiz+yozma umumiy musobaqani tanlaydi. Quiz+yozma turida quiz va yozma savollar soni hamda vaqt sozlamalari alohida belgilanadi; bitta kod ishlatiladi, quiz birinchi boshlanadi, so‘ng yozma qism 10 soniyalik tayyorgarlikdan keyin ishga tushadi.

## Diplom PDF

Diplom PDF shaklida yuboriladi. Yaratuvchi diplom dizaynini va matnini o‘zgartira oladi, mezonni o‘zi belgilaydi. Diplomda loyiha muallifi va kanal havolasi majburiy ko‘rsatilmaydi.

## Faol test kodlari

Faol musobaqa kodlari bir vaqtda takrorlanmaydi. Takror kod kiritilsa, bot yangi kod so‘raydi. Sessiya tugagach kod faolsizlanadi; test qayta ishga tushirilganda yangi sessiya yaratiladi.

## Test eksporti

QuizBot’ga eksport qilish funksiyasi qo‘shilmaydi. Yaratuvchi quiz, yozma yoki aralash testni PDF shaklida oladi. Yozma PDF’da javob yozish joylari bo‘ladi. To‘g‘ri javoblarni ko‘rsatish, alohida kalit qilish yoki yashirish tanlanadi. Test tugagach, yaratuvchi PDF’ni qatnashchilarga yuborishi mumkin.

## Yakka test

Har bir test uchun alohida doimiy yakka test kodi mavjud bo‘ladi. Kod kiritilgach test darhol boshlanadi. Foydalanuvchi istalgancha urinish qiladi; har bir urinish natijasi ko‘rsatiladi, rasmiy saqlanadigan ko‘rsatkich esa faqat eng yaxshi natija bo‘ladi.

## Ko‘p tillilik

Interfeys o‘zbek, rus, ingliz, xitoy, fransuz, koreys, yapon, qozoq, tojik, turk, arab, nemis, ispan, portugal, italyan, hind, urdu, bengal, indonez va vetnam tillarini qo‘llab-quvvatlaydi. Yaratuvchi kiritgan savol va javoblar avtomatik tarjima qilinmaydi.

## Vaqt mintaqasi va boshlanish vaqti

Test yaratuvchi Mini App’da boshlanish sanasi va vaqtini tanlagich orqali belgilaydi; sana, soat va daqiqani qo‘lda murakkab formatda yozish shart emas. Shuningdek, davlat va shaharlar ro‘yxatidan vaqt mintaqasi tanlanadi. Ro‘yxatda mamlakat nomi, shahar nomi va UTC farqi ko‘rsatiladi; O‘zbekiston uchun Toshkent (UTC+5) mavjud bo‘ladi. Bot vaqtlarni ichki ravishda umumiy standartda saqlaydi va foydalanuvchilarga tanlangan vaqt mintaqasiga mos ko‘rsatadi.

## Mualliflik va kanal

Bot tavsifida “Loyiha muallifi: Gulmira Norpulatova. Loyihalashtiruvchi: AI.” matni hamda https://t.me/FAKTastika1 havolasi bo‘ladi. Diplom PDF’larida esa muallif va kanal havolasi bo‘lmaydi.

## Natijalar va reyting

Test yakunida qatnashchiga to‘g‘ri, xato va javobsiz javoblar, foiz, savollar, tanlangan javoblar va to‘g‘ri javoblar ko‘rsatiladi. Yaratuvchi reytingni ko‘radi va xohlasa natijalarni barcha qatnashchilarga ochadi. Mezonga javob bergan qatnashchilarga yaratuvchi sozlagan diplomlar avtomatik yuboriladi.

## Tahrirlash

Yaratuvchi o‘z testining savollar banki va keyingi ishga tushirish sozlamalarini Mini App orqali tahrirlay oladi. Tahrirlashdan oldin bot tasdiqlash oynasini ko‘rsatadi. Faol yoki tugagan sessiya tahrirlanmaydi; o‘zgartirilgan savollar yoki sozlamalar keyingi yangi sessiyada qo‘llanadi. Faol testga o‘zgartirish kerak bo‘lsa, avval sessiya tugatiladi yoki yangi sessiya yaratiladi.

## Tahrirlash xavfsizligi

Tahrirlash va o‘chirish faqat test yaratuvchisiga ruxsat etiladi. O‘chirish ikki bosqichli tasdiq bilan bajariladi, tahrirlash esa o‘zgarishlarni saqlashdan oldin yakuniy ko‘rib chiqish oynasini ko‘rsatadi.

## Testni bekor qilish

Yaratuvchi hali boshlanmagan rejalashtirilgan umumiy test sessiyasini alohida **Testni bekor qilish** tugmasi orqali bekor qila oladi. Bot bekor qilishdan oldin tasdiq so‘raydi. Tasdiqlangandan keyin sessiya ishga tushmaydi, uning faol kodi faolsizlanadi va ro‘yxatdan o‘tgan qatnashchilarga test bekor qilingani haqida xabar yuboriladi. Test banki, savollar va avvalgi natijalar o‘chirilmaydi; yaratuvchi keyinchalik yangi sessiya yaratib testni qayta ishga tushira oladi.

## Tilni tanlash menyusi

Asosiy menyuda doimiy **Tilni tanlash** tugmasi bo‘ladi. Foydalanuvchi istalgan payt 20 ta til ro‘yxatini qayta ochib, boshqa tilni tanlay oladi. Tanlov darhol foydalanuvchi profiliga saqlanadi va keyingi bot xabarlari yangi tilda ko‘rsatiladi.

## Qo‘shimcha sifat va ishonchlilik talablari

Yaratuvchi testni e’lon qilishdan oldin savollar va sozlamalarni ko‘rib chiqadi hamda sessiyani boshlashni alohida tasdiqlaydi. Vaqt tugaganda javoblar avtomatik topshiriladi; Telegram callback yoki foydalanuvchi xabari takror yuborilsa, ikkinchi marta ball berilmaydi. Natijalar durang holatlarida bir xil o‘rinlarni to‘g‘ri ko‘rsatadi.

Yakka test urinishlari alohida saqlanadi va eng yaxshi natija ajratib ko‘rsatiladi. Bot qayta ishga tushganda faol sessiya holati bazadan tiklanadi. Natijalarni qo‘shimcha CSV ko‘rinishida olish imkoniyati ko‘zda tutiladi. Administrator uchun maxfiy ma’lumotlarsiz texnik xatolar jurnali saqlanadi.
