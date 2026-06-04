"""
Scraper — Skill extraction and text parsing utilities.

Contains a comprehensive skills database and functions to parse
job descriptions for skills, salary, experience level, and work type.
"""

import re
from typing import Optional

# ─────────────────────────────────────────────
#  Master Skills Database (100+ skills)
# ─────────────────────────────────────────────

SKILL_KEYWORDS = {
    # Programming Languages
    "Python": ["python", "python3", "py"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java", "jvm"],
    "C++": ["c++", "cpp", "c plus plus"],
    "C#": ["c#", "csharp", "c sharp", ".net"],
    "Go": ["golang", "go lang"],
    "Rust": ["rust", "rustlang"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "Scala": ["scala"],
    "R": ["r programming", "r language", "rstudio"],
    "MATLAB": ["matlab"],
    "Perl": ["perl"],
    "Dart": ["dart"],
    "Lua": ["lua"],
    "Shell": ["bash", "shell", "zsh", "powershell"],

    # Web Frameworks
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi", "fast api"],
    "React": ["react", "reactjs", "react.js"],
    "Vue.js": ["vue", "vuejs", "vue.js"],
    "Angular": ["angular", "angularjs"],
    "Next.js": ["next.js", "nextjs"],
    "Nuxt.js": ["nuxt", "nuxtjs", "nuxt.js"],
    "Express.js": ["express", "expressjs", "express.js"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Spring": ["spring", "spring boot", "springboot"],
    "Rails": ["rails", "ruby on rails"],
    "Laravel": ["laravel"],
    "ASP.NET": ["asp.net", "aspnet", "asp net"],
    "Svelte": ["svelte", "sveltekit"],
    "Remix": ["remix"],

    # Databases
    "SQL": ["sql", "structured query language"],
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "elastic"],
    "SQLite": ["sqlite"],
    "Oracle": ["oracle db", "oracle database"],
    "DynamoDB": ["dynamodb", "dynamo db"],
    "Cassandra": ["cassandra"],
    "Neo4j": ["neo4j"],
    "Firebase": ["firebase", "firestore"],

    # DevOps & Tools
    "Docker": ["docker", "dockerfile", "docker-compose"],
    "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "Jenkins": ["jenkins"],
    "GitHub Actions": ["github actions"],
    "GitLab CI": ["gitlab ci", "gitlab-ci"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],
    "Nginx": ["nginx"],
    "Apache": ["apache"],
    "Linux": ["linux", "ubuntu", "centos", "debian"],
    "Git": ["git", "github", "gitlab", "bitbucket"],
    "Prometheus": ["prometheus"],
    "Grafana": ["grafana"],

    # Cloud
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "sqs", "sns"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Heroku": ["heroku"],
    "Vercel": ["vercel"],
    "DigitalOcean": ["digitalocean", "digital ocean"],

    # Data Science & ML
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "TensorFlow": ["tensorflow", "tf"],
    "PyTorch": ["pytorch"],
    "Scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "cv", "opencv"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Data Engineering": ["data engineering", "data pipeline"],
    "Apache Spark": ["spark", "apache spark", "pyspark"],
    "Hadoop": ["hadoop"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "LLM": ["llm", "large language model", "gpt", "chatgpt"],
    "AI": ["artificial intelligence", "ai"],

    # Mobile
    "React Native": ["react native"],
    "Flutter": ["flutter"],
    "iOS": ["ios", "iphone"],
    "Android": ["android"],
    "SwiftUI": ["swiftui"],

    # Frontend
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "Sass": ["sass", "scss"],
    "Tailwind CSS": ["tailwind", "tailwindcss", "tailwind css"],
    "Bootstrap": ["bootstrap"],
    "jQuery": ["jquery"],
    "Webpack": ["webpack"],
    "Vite": ["vite"],

    # Testing
    "Unit Testing": ["unit test", "unit testing", "unittest"],
    "Jest": ["jest"],
    "Pytest": ["pytest"],
    "Selenium": ["selenium"],
    "Cypress": ["cypress"],
    "Playwright": ["playwright"],

    # Architecture & Patterns
    "REST API": ["rest", "restful", "rest api"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "micro services"],
    "System Design": ["system design"],
    "Design Patterns": ["design patterns"],
    "Agile": ["agile", "scrum", "kanban"],
    "DevOps": ["devops"],

    # Security
    "Cybersecurity": ["cybersecurity", "cyber security", "security"],
    "OAuth": ["oauth", "oauth2"],
    "JWT": ["jwt", "json web token"],

    # Other
    "API": ["api", "apis"],
    "Blockchain": ["blockchain"],
    "IoT": ["iot", "internet of things"],
    "WebSocket": ["websocket", "websockets"],
    "gRPC": ["grpc"],
    "RabbitMQ": ["rabbitmq", "rabbit mq"],
    "Celery": ["celery"],
    "Apache Kafka": ["kafka", "apache kafka"],
    "Figma": ["figma"],
    "Jira": ["jira"],
}


def extract_skills_from_text(text: str) -> list[str]:
    """
    Extract skills from a job description by keyword matching.
    Returns a list of unique skill names found in the text.
    """
    if not text:
        return []

    text_lower = text.lower()
    found_skills = set()

    for skill_name, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundary matching to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill_name)
                break  # Found this skill, move to next

    return sorted(found_skills)


def get_skill_category(skill_name: str) -> str:
    """Return the category for a given skill name."""
    programming = ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Perl", "Dart", "Shell"]
    frameworks = ["Django", "Flask", "FastAPI", "React", "Vue.js", "Angular", "Next.js", "Node.js", "Spring", "Rails", "Laravel", "Express.js", "Svelte"]
    databases = ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "DynamoDB", "Cassandra", "Firebase"]
    devops = ["Docker", "Kubernetes", "CI/CD", "Jenkins", "Terraform", "Ansible", "Nginx", "Git", "Linux", "Prometheus", "Grafana"]
    cloud = ["AWS", "Azure", "GCP", "Heroku", "Vercel", "DigitalOcean"]
    data_science = ["Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "NLP", "Computer Vision", "Data Analysis", "AI", "LLM"]

    if skill_name in programming:
        return "Programming"
    elif skill_name in frameworks:
        return "Framework"
    elif skill_name in databases:
        return "Database"
    elif skill_name in devops:
        return "DevOps"
    elif skill_name in cloud:
        return "Cloud"
    elif skill_name in data_science:
        return "Data Science"
    return "Other"


def parse_salary(text: str) -> dict:
    """
    Parse salary range from text.
    Returns dict with min, max, currency.
    """
    if not text:
        return {"min": None, "max": None, "currency": "USD"}

    # Clean the text
    text = text.replace(",", "").replace(" ", "")

    # Detect currency
    currency = "USD"
    currency_map = {
        "৳": "BDT", "tk": "BDT", "bdt": "BDT", "taka": "BDT",
        "$": "USD", "usd": "USD",
        "€": "EUR", "eur": "EUR",
        "£": "GBP", "gbp": "GBP",
        "₹": "INR", "inr": "INR",
    }
    for symbol, curr in currency_map.items():
        if symbol in text.lower():
            currency = curr
            break

    # Try to find salary range patterns
    patterns = [
        r'(\d+)\s*[-–—to]+\s*(\d+)',  # "3000 - 5000" or "3000 to 5000"
        r'(\d+)k\s*[-–—to]+\s*(\d+)k',  # "3k - 5k"
        r'(\d+)',  # Single number
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            groups = match.groups()
            if len(groups) == 2:
                min_val = int(groups[0])
                max_val = int(groups[1])
                # Handle "k" suffix
                if "k" in text.lower():
                    min_val *= 1000
                    max_val *= 1000
                return {"min": min_val, "max": max_val, "currency": currency}
            elif len(groups) == 1:
                val = int(groups[0])
                if "k" in text.lower():
                    val *= 1000
                return {"min": val, "max": None, "currency": currency}

    return {"min": None, "max": None, "currency": currency}


def parse_experience_level(text: str) -> str:
    """
    Determine experience level from job description or title.
    Returns: 'Entry', 'Mid', 'Senior', 'Lead', 'Director', or ''
    """
    if not text:
        return ""

    text_lower = text.lower()

    # Check from most to least senior
    if any(kw in text_lower for kw in ["director", "vp ", "vice president", "head of", "chief"]):
        return "Director"
    if any(kw in text_lower for kw in ["lead", "principal", "staff", "architect"]):
        return "Lead"
    if any(kw in text_lower for kw in ["senior", "sr.", "sr ", "experienced", "5+ years", "7+ years", "10+ years"]):
        return "Senior"
    if any(kw in text_lower for kw in ["mid", "middle", "intermediate", "2+ years", "3+ years", "4+ years"]):
        return "Mid"
    if any(kw in text_lower for kw in ["junior", "jr.", "jr ", "entry", "intern", "trainee", "graduate", "fresher", "0-1 year", "0-2 year", "1+ year"]):
        return "Entry"

    return ""


def parse_work_type(text: str) -> str:
    """
    Determine work type from location text or job description.
    Returns: 'Remote', 'Hybrid', or 'On-site'
    """
    if not text:
        return "On-site"

    text_lower = text.lower()

    if any(kw in text_lower for kw in ["remote", "work from home", "wfh", "anywhere", "worldwide"]):
        if "hybrid" in text_lower:
            return "Hybrid"
        return "Remote"
    if "hybrid" in text_lower:
        return "Hybrid"
    if any(kw in text_lower for kw in ["on-site", "onsite", "on site", "in-office", "in office"]):
        return "On-site"

    return "On-site"
