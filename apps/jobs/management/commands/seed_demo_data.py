"""
Django management command to seed realistic demo data for CareerBridge.
Seeds Companies, Skills, JobPosts, and JobSkills.
"""

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.jobs.models import Company, Skill, JobPost, JobSkill


class Command(BaseCommand):
    help = "Seeds the database with 50+ realistic demo companies, skills, and job postings."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        with transaction.atomic():
            # Clear existing data to ensure idempotency and clean start
            self.stdout.write("Clearing existing jobs, companies, and skills...")
            JobSkill.objects.all().delete()
            JobPost.objects.all().delete()
            Company.objects.all().delete()
            Skill.objects.all().delete()

            # 1. Create Companies
            companies_data = [
                {"name": "Google", "industry": "Technology / Internet", "website": "https://google.com"},
                {"name": "Meta", "industry": "Social Media / Technology", "website": "https://meta.com"},
                {"name": "Brain Station 23", "industry": "Software Development", "website": "https://brainstation-23.com"},
                {"name": "BJIT Group", "industry": "IT Services & Consultancy", "website": "https://bjitgroup.com"},
                {"name": "Bdjobs.com", "industry": "Internet / Jobs Board", "website": "https://bdjobs.com"},
                {"name": "Selise", "industry": "Software Development", "website": "https://selise.ch"},
                {"name": "Cefalo", "industry": "Offshore Software Development", "website": "https://cefalo.com"},
                {"name": "Therap Services", "industry": "Healthcare IT", "website": "https://therapservices.net"},
                {"name": "Enosis Solutions", "industry": "Software Engineering", "website": "https://enosis.com"},
                {"name": "bKash", "industry": "FinTech / Financial Services", "website": "https://bkash.com"},
                {"name": "Pathao", "industry": "Ride-sharing & Logistics", "website": "https://pathao.com"},
                {"name": "Chaldal", "industry": "E-commerce / Retail", "website": "https://chaldal.com"},
                {"name": "Datasoft", "industry": "Systems Integration & Software", "website": "https://datasoft-bd.com"},
                {"name": "Kaz Software", "industry": "Custom Software Development", "website": "https://kaz.com.bd"},
                {"name": "SSL Wireless", "industry": "Telecommunications & FinTech", "website": "https://sslwireless.com"},
            ]

            companies = []
            for c in companies_data:
                comp = Company.objects.create(
                    name=c["name"],
                    industry=c["industry"],
                    website=c["website"],
                    linkedin_id=f"linkedin-co-{random.randint(100000, 999999)}",
                    logo_url=f"https://placehold.co/100x100?text={c['name'].replace(' ', '+')}"
                )
                companies.append(comp)

            # 2. Create Skills
            skills_data = [
                # Programming
                ("Python", "Programming"),
                ("JavaScript", "Programming"),
                ("TypeScript", "Programming"),
                ("Go", "Programming"),
                ("Java", "Programming"),
                ("C++", "Programming"),
                ("Ruby", "Programming"),
                ("SQL", "Programming"),
                # Frameworks
                ("Django", "Framework"),
                ("Flask", "Framework"),
                ("FastAPI", "Framework"),
                ("React", "Framework"),
                ("Vue", "Framework"),
                ("Angular", "Framework"),
                ("Node.js", "Framework"),
                ("Express.js", "Framework"),
                ("Spring Boot", "Framework"),
                # Databases
                ("PostgreSQL", "Database"),
                ("MongoDB", "Database"),
                ("Redis", "Database"),
                ("MySQL", "Database"),
                # DevOps
                ("Docker", "DevOps"),
                ("Kubernetes", "DevOps"),
                ("CI/CD", "DevOps"),
                ("Terraform", "DevOps"),
                ("GitHub Actions", "DevOps"),
                # Cloud
                ("AWS", "Cloud"),
                ("Azure", "Cloud"),
                ("GCP", "Cloud"),
                # Data Science
                ("TensorFlow", "Data Science"),
                ("PyTorch", "Data Science"),
                ("Pandas", "Data Science"),
                ("NumPy", "Data Science"),
                ("Machine Learning", "Data Science"),
                # Design
                ("Figma", "Design"),
                ("UI/UX", "Design"),
                # Soft Skill
                ("Agile", "Soft Skill"),
                ("Communication", "Soft Skill"),
                ("Teamwork", "Soft Skill"),
                ("Project Management", "Soft Skill"),
            ]

            skills = {}
            for name, cat in skills_data:
                skill = Skill.objects.create(name=name, category=cat)
                skills[name] = skill

            # 3. Create Job Posts
            job_titles = [
                ("Software Engineer", ["Python", "Django", "PostgreSQL", "Docker", "Agile"]),
                ("Python Developer", ["Python", "Django", "FastAPI", "SQL", "Git"]),
                ("Backend Developer", ["Go", "Node.js", "Redis", "Docker", "CI/CD"]),
                ("Full Stack Developer", ["JavaScript", "TypeScript", "React", "Node.js", "MongoDB"]),
                ("Frontend Engineer", ["JavaScript", "TypeScript", "React", "Vue", "Figma"]),
                ("DevOps Engineer", ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD"]),
                ("Cloud Solutions Architect", ["AWS", "GCP", "Kubernetes", "Terraform", "Communication"]),
                ("Data Scientist", ["Python", "Pandas", "NumPy", "Machine Learning", "SQL"]),
                ("ML Engineer", ["Python", "PyTorch", "TensorFlow", "Machine Learning", "Docker"]),
                ("Junior Web Developer", ["JavaScript", "React", "SQL", "Teamwork"]),
                ("Senior Software Engineer", ["Python", "Django", "Docker", "AWS", "Agile", "Communication"]),
                ("Technical Lead", ["Go", "Kubernetes", "AWS", "Agile", "Project Management", "Communication"]),
            ]

            work_types = ["Remote", "Hybrid", "On-site"]
            exp_levels = ["Entry", "Mid", "Senior", "Lead"]
            statuses = ["new", "saved", "applied", "ignored"]
            locations = [
                "Dhaka, Bangladesh",
                "Remote (Worldwide)",
                "Hybrid (Dhaka)",
                "Chittagong, Bangladesh",
                "Sylhet, Bangladesh",
                "Remote (Bangladesh)",
            ]

            # We need 50+ posts
            total_posts = 55
            today = date.today()

            for i in range(total_posts):
                title_template, required_skill_names = random.choice(job_titles)
                company = random.choice(companies)
                work_type = random.choice(work_types)
                exp_level = random.choice(exp_levels)
                
                # Determine salary based on experience level
                if exp_level == "Entry":
                    salary_min = random.randint(500, 1200)
                    salary_max = salary_min + random.randint(300, 800)
                elif exp_level == "Mid":
                    salary_min = random.randint(1500, 3000)
                    salary_max = salary_min + random.randint(1000, 2000)
                elif exp_level == "Senior":
                    salary_min = random.randint(3500, 6000)
                    salary_max = salary_min + random.randint(1500, 3000)
                else:  # Lead
                    salary_min = random.randint(6500, 9000)
                    salary_max = salary_min + random.randint(2000, 4000)

                # Salary displays USD/BDT/EUR
                currency = random.choice(["USD", "BDT", "EUR"])
                if currency == "BDT":
                    salary_min *= 115
                    salary_max *= 115

                # Location matches work type
                if work_type == "Remote":
                    location = random.choice(["Remote (Worldwide)", "Remote (Bangladesh)"])
                elif work_type == "Hybrid":
                    location = "Dhaka (Hybrid)"
                else:
                    location = random.choice(["Dhaka, Bangladesh", "Chittagong, Bangladesh", "Sylhet, Bangladesh"])

                # Date posted
                days_ago = random.randint(0, 30)
                date_posted = today - timedelta(days=days_ago)

                # Status distribution
                # Mostly new, some saved, applied, ignored
                status = random.choices(statuses, weights=[0.6, 0.15, 0.15, 0.1], k=1)[0]

                job = JobPost.objects.create(
                    linkedin_job_id=f"linkedin-job-{random.randint(1000000000, 9999999999)}",
                    title=f"{exp_level} {title_template}" if "Junior" not in title_template and "Senior" not in title_template else title_template,
                    company=company,
                    location=location,
                    work_type=work_type,
                    description=(
                        f"We are looking for a {title_template} to join our growing team. "
                        f"As part of this role, you will work on key projects and collaborate with cross-functional teams. "
                        f"The ideal candidate has strong expertise in: {', '.join(required_skill_names)}.\n\n"
                        f"Requirements:\n"
                        f"- Experience working as a {title_template} or similar role.\n"
                        f"- Hands-on experience with: {', '.join(required_skill_names[:3])}.\n"
                        f"- Strong problem-solving and communication skills.\n"
                        f"- Ability to work in an Agile environment."
                    ),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency,
                    experience_level=exp_level,
                    date_posted=date_posted,
                    apply_url=f"https://linkedin.com/jobs/view/{random.randint(1000000000, 9999999999)}",
                    status=status,
                    is_active=True
                )

                # Associate skills
                for skill_name in required_skill_names:
                    if skill_name in skills:
                        JobSkill.objects.create(job=job, skill=skills[skill_name])

                # Random extra skills
                extra_skills = random.sample(list(skills.values()), k=random.randint(1, 3))
                for es in extra_skills:
                    if es.name not in required_skill_names:
                        JobSkill.objects.get_or_create(job=job, skill=es)

            # Override scraped_at dates to spread them over the month for over-time charts
            # (since Django's auto_now_add is hard to set on create, we update afterward)
            for i, job in enumerate(JobPost.objects.all()):
                # Distribute scraped_at over 30 days
                days_back = random.randint(0, 30)
                job.scraped_at = timezone.now() - timedelta(days=days_back, hours=random.randint(0, 23))
                job.save(update_fields=["scraped_at"])

            self.stdout.write(self.style.SUCCESS(f"Successfully seeded {total_posts} job postings!"))
