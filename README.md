# دليل استخدام الذكاء الاصطناعي — ai.watnia.com

صفحة تعليمية عربية واحدة تشرح استخدام Claude وChatGPT وQwen وMiniMax.
مستضافة على GitHub Pages خلف Cloudflare.

## الملفات

| الملف | الغرض |
|---|---|
| `index.html` | الصفحة كاملة (HTML + CSS + JS في ملف واحد — بلا خطوة بناء) |
| `news.json` | الأخبار المعروضة. **مولَّد آلياً — لا تعدّله يدوياً** |
| `curated.json` | أخبار Claude وMiniMax. **عدّله يدوياً** (لا تنشر الشركتان RSS) |
| `scripts/fetch_news.py` | يسحب التغذيات ويدمجها مع `curated.json` ويكتب `news.json` |
| `.github/workflows/update-news.yml` | يشغّل السكربت كل اثنين، ويحفظ التغيير إن وُجد |
| `CNAME` | النطاق: `ai.watnia.com` |

## كيف تُحدَّث الأخبار

- **آلياً**: OpenAI وQwen عبر RSS رسمي — كل اثنين 05:00 UTC.
- **يدوياً**: Claude وMiniMax عبر `curated.json` — عدّله من GitHub مباشرةً، ثم شغّل
  التحديث من تبويب **Actions ▸ تحديث الأخبار ▸ Run workflow**.

السكربت **لا يُفرغ الصفحة أبداً**: إن فشل مصدر، يُبقي أخباره السابقة؛ وإن فشل كل شيء،
يترك `news.json` كما هو.

## خطوات النشر (مرة واحدة)

### 1. المستودع
```bash
cd ai-guide
git init -b main
git add .
git commit -m "دليل استخدام الذكاء الاصطناعي"
git remote add origin https://github.com/ahmedhd123/ai-guide.git
git push -u origin main
```

### 2. GitHub Pages
`Settings ▸ Pages` ← Source: **Deploy from a branch** ← Branch: **main** / **/ (root)** ← Save.

### 3. Cloudflare DNS
`DNS ▸ Records ▸ Add record`:

| النوع | الاسم | الوجهة | البروكسي |
|---|---|---|---|
| CNAME | `ai` | `ahmedhd123.github.io` | **DNS only** (سحابة رمادية) مبدئياً |

### 4. الشهادة — ⚠️ الترتيب مهم
1. اترك البروكسي **معطّلاً** (رمادي) حتى يُصدر GitHub شهادة SSL (دقائق إلى ساعة).
2. في `Settings ▸ Pages` تأكّد أن الحقل يعرض `ai.watnia.com` بلا تحذير، ثم فعّل **Enforce HTTPS**.
3. بعدها فقط: فعّل البروكسي (سحابة برتقالية) واضبط
   `SSL/TLS ▸ Overview` على **Full** (وليس Flexible — تسبّب إعادة توجيه لانهائية).

### 5. الربط من الموقع
أضف رابطاً إلى `https://ai.watnia.com` من تذييل watnia.com أو قسم الذكاء الاصطناعي.

## معاينة محلية
```bash
python -m http.server 4173
```
ثم افتح `http://127.0.0.1:4173`.
(لا تفتح `index.html` مباشرةً بنقرة مزدوجة — `fetch` للأخبار يحتاج خادماً.)
