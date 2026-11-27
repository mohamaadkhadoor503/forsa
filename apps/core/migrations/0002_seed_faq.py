from django.db import migrations

FAQS = [
    ("هل التسجيل في المنصة مجاني؟", "نعم، إنشاء الحساب والتقديم على الوظائف والمشاريع مجاني بالكامل للباحثين عن عمل والمستقلين.",
     "Is registration free?", "Yes. Creating an account and applying to jobs and projects is completely free for job seekers and freelancers."),
    ("ما الفرق بين الوظيفة والمشروع؟", "الوظيفة فرصة عمل بدوام كامل أو جزئي لدى شركة، أما المشروع فمهمة محددة بميزانية ومدة تنفيذ يتم إسنادها لمستقل.",
     "What is the difference between a job and a project?", "A job is a full or part-time position at a company, while a project is a defined task with a budget and timeline awarded to a freelancer."),
    ("كيف أتابع حالة طلب التوظيف؟", "من لوحة التحكم ← طلباتي، ستجد خطاً زمنياً يوضح كل مرحلة، وستصلك إشعارات عند أي تحديث.",
     "How do I track my application?", "Go to Dashboard → My applications. A timeline shows each stage and you'll be notified of every update."),
    ("كيف أنشر وظيفة أو مشروعاً؟", "سجّل كصاحب عمل، ثم من لوحة التحكم اختر «نشر وظيفة» أو «نشر مشروع» واملأ التفاصيل.",
     "How do I post a job or project?", "Register as an employer, then choose “Post a job” or “Post a project” from your dashboard."),
    ("كيف يتم احتساب التقييمات؟", "لا يمكن لأحد تقييم مستقل إلا صاحب المشروع الذي أنجزه المستقل فعلياً، لضمان أن جميع التقييمات حقيقية.",
     "How are ratings calculated?", "Only the owner of a project that a freelancer actually completed can rate them, so every rating is genuine."),
    ("كيف أبلغ عن محتوى مخالف؟", "استخدم زر «إبلاغ» الموجود في صفحة الوظيفة أو المشروع أو الملف الشخصي، وسيراجع فريقنا البلاغ.",
     "How do I report inappropriate content?", "Use the “Report” button on any job, project or profile page and our team will review it."),
]


def seed(apps, schema_editor):
    FAQ = apps.get_model("core", "FAQ")
    for i, (q, a, qe, ae) in enumerate(FAQS):
        FAQ.objects.get_or_create(question=q, defaults={"answer": a, "question_en": qe, "answer_en": ae, "order": i})
    apps.get_model("core", "SiteSettings").objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
