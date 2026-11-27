# فرصة — منصة التوظيف والعمل الحر (Django + PostgreSQL)

منصة عربية تربط الباحثين عن عمل والمستقلين بالشركات وأصحاب المشاريع: نشر وظائف ومشاريع، تقديم ومتابعة الطلبات بخط زمني، عروض على المشاريع، محادثات، إشعارات، تقييمات حقيقية، بلاغات، ولوحات تحكم لثلاثة أدوار.

## التشغيل السريع (Windows)

```powershell
cd "D:\مشروع دجانكو"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # ثم عدّل بيانات PostgreSQL داخل .env
python manage.py migrate
python manage.py createsuperuser   # حساب المدير (بالبريد الإلكتروني)
python manage.py runserver
```
افتح: http://127.0.0.1:8000

### قاعدة البيانات PostgreSQL
1. ثبّت PostgreSQL (أو `docker compose up -d` إن كان Docker مثبتاً).
2. أنشئ قاعدة بيانات: `CREATE DATABASE jobboard;`
3. ضع بيانات الاتصال في `.env` (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`).

للتجربة السريعة بدون PostgreSQL فقط: أضف `DB_ENGINE=sqlite` في `.env`.

### بيانات تجريبية (للاختبار المحلي فقط)
```powershell
python manage.py seed_demo          # إنشاء
python manage.py seed_demo --clear  # حذف
```
كل الحسابات التجريبية كلمة مرورها `Demo@12345`:
| الدور | البريد |
|---|---|
| مدير المنصة | admin@demo.local |
| صاحب عمل | employer1@demo.local |
| باحث عن عمل | seeker1@demo.local |

المحتوى التجريبي موسوم بـ «(تجريبي)» ولا يُستخدم في الإنتاج.

### الاختبارات
```powershell
python manage.py test tests
```

### الترجمة (عربي/إنجليزي)
النصوص المصدرية عربية، والترجمة الإنجليزية في `scripts/translations_en.py`. بعد تعديل أي نص:
```powershell
python scripts/i18n.py extract   # يعرض النصوص غير المترجمة
python scripts/i18n.py build     # يبني ملفات .po و .mo
```
(لا يحتاج GNU gettext.)

## البنية المعمارية
```
config/settings/{base,dev,prod}.py   إعدادات حسب البيئة من متغيرات البيئة
apps/
  core/          النماذج الأساسية، الفلترة القابلة للتركيب، الإحصائيات، الصفحات العامة، القوالب المساعدة
  accounts/      مستخدم مخصص (دخول بالبريد) + أدوار + خدمة التسجيل
  jobs/          التصنيفات، المهارات، الوظائف، الحفظ، التوصيات
  companies/     الشركات والمرشحون المفضلون
  talents/       الملف المهني، الخبرات، التعليم، معرض الأعمال، نسبة الاكتمال
  applications/  طلبات التوظيف + سجل الحالات (Timeline)
  projects/      المشاريع الحرة والعروض
  messaging/     المحادثات
  notifications/ الإشعارات (قنوات قابلة للتوسعة)
  reviews/       التقييمات، آراء المستخدمين، البلاغات
  dashboard/     لوحات الباحث / صاحب العمل / الإدارة
```


