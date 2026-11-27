"""Reference data: the platform's job categories and common skills."""
from django.db import migrations

CATEGORIES = [
    ("البرمجة وتطوير المواقع", "Programming & Web Development", "programming", "code", "#2563EB"),
    ("الأمن السيبراني", "Cybersecurity", "cybersecurity", "shield", "#0EA5E9"),
    ("التصميم الجرافيكي", "Graphic Design", "graphic-design", "palette", "#EC4899"),
    ("التسويق الرقمي", "Digital Marketing", "digital-marketing", "megaphone", "#F59E0B"),
    ("الهندسة", "Engineering", "engineering", "cog", "#64748B"),
    ("المحاسبة والمالية", "Accounting & Finance", "finance", "calculator", "#10B981"),
    ("المونتاج وصناعة المحتوى", "Video Editing & Content", "content", "film", "#EF4444"),
    ("الذكاء الاصطناعي", "Artificial Intelligence", "ai", "cpu", "#7C3AED"),
    ("الإدارة والأعمال", "Management & Business", "business", "chart", "#06B6D4"),
    ("العمل عن بعد", "Remote Work", "remote", "wifi", "#14B8A6"),
]

SKILLS = [
    "Python", "Django", "JavaScript", "React", "Vue.js", "Node.js", "PHP", "Laravel", "Flutter", "SQL",
    "PostgreSQL", "Docker", "AWS", "Figma", "Photoshop", "Illustrator", "UI/UX", "SEO",
    "تسويق عبر وسائل التواصل", "كتابة المحتوى", "مونتاج الفيديو", "Premiere Pro", "After Effects",
    "تحليل البيانات", "Machine Learning", "Excel", "المحاسبة", "إدارة المشاريع", "AutoCAD", "اختبار الاختراق",
]


def seed(apps, schema_editor):
    Category = apps.get_model("jobs", "Category")
    Skill = apps.get_model("jobs", "Skill")
    for order, (name, name_en, slug, icon, color) in enumerate(CATEGORIES):
        Category.objects.get_or_create(slug=slug, defaults={
            "name": name, "name_en": name_en, "icon": icon, "color": color, "order": order})
    from django.utils.text import slugify
    for name in SKILLS:
        slug = slugify(name, allow_unicode=True) or name
        Skill.objects.get_or_create(name=name, defaults={"slug": slug})


def unseed(apps, schema_editor):
    apps.get_model("jobs", "Category").objects.filter(slug__in=[c[2] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [("jobs", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
