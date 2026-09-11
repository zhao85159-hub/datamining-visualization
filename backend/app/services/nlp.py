"""Skills-extraction NLP module.

Given free-text job descriptions, this module extracts a normalised set of
professional skills using a curated skill gazetteer combined with tokenisation
and lemmatisation (NLTK).  It is independent of the dataset's own
``job_skills`` mapping: the dataset stores coarse skill *abbreviations*, whereas
this module mines fine-grained skills (tools, languages, frameworks, soft
skills) directly from the unstructured ``description`` field.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

# Canonical skill -> list of surface aliases (matched case-insensitively, on
# word boundaries).  Curated from common occurrences in technology, data,
# business and soft-skill vocabularies.
SKILL_GAZETTEER: dict[str, list[str]] = {
    "Python": ["python"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "es6"],
    "TypeScript": ["typescript", "ts"],
    "C++": [r"c\+\+", "cpp"],
    "C#": [r"c#", "c sharp", "csharp"],
    "Go": ["golang", "go lang"],
    "Rust": ["rust"],
    "PHP": ["php"],
    "Ruby": ["ruby", "ruby on rails", "rails"],
    "Scala": ["scala"],
    "R": ["r programming", "rstats"],
    "SQL": ["sql", "t-sql", "pl/sql"],
    "NoSQL": ["nosql"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3", "sass", "scss"],
    "React": ["react", "react.js", "reactjs"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Angular": ["angular", "angularjs"],
    "Node.js": ["node", "node.js", "nodejs"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Spring": ["spring", "spring boot"],
    ".NET": [r"\.net", "dotnet", "asp.net"],
    "Express.js": ["express", "express.js"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Oracle": ["oracle db", "oracle database"],
    "SQL Server": ["sql server", "mssql"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "Jenkins": ["jenkins"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration"],
    "Git": ["git", "github", "gitlab", "version control"],
    "Linux": ["linux", "unix", "bash", "shell scripting"],
    "Machine Learning": ["machine learning", "ml", "scikit-learn", "sklearn"],
    "Deep Learning": ["deep learning", "neural network"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv"],
    "Data Analysis": ["data analysis", "data analytics", "analytics"],
    "Data Science": ["data science", "data scientist"],
    "Data Engineering": ["data engineering", "etl", "data pipeline"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Spark": ["spark", "pyspark", "apache spark"],
    "Hadoop": ["hadoop"],
    "Kafka": ["kafka"],
    "Airflow": ["airflow"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel", "microsoft excel", "spreadsheet"],
    "Statistics": ["statistics", "statistical analysis"],
    "Data Visualisation": ["data visualization", "data visualisation", "dashboard"],
    "REST API": ["rest", "rest api", "restful", "api development"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "microservice"],
    "Agile": ["agile", "scrum", "kanban"],
    "DevOps": ["devops"],
    "Testing": ["testing", "qa", "unit testing", "selenium", "pytest", "junit"],
    "Cybersecurity": ["cybersecurity", "security", "penetration testing", "infosec"],
    "Networking": ["networking", "tcp/ip", "network administration"],
    "UI/UX": ["ui/ux", "ux", "user experience", "figma", "sketch"],
    "Project Management": ["project management", "pmp", "prince2"],
    "Product Management": ["product management", "product manager"],
    "Communication": ["communication", "communication skills"],
    "Leadership": ["leadership", "team lead", "mentoring"],
    "Teamwork": ["teamwork", "collaboration", "team player"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical skills"],
    "Time Management": ["time management"],
    "Marketing": ["marketing", "seo", "sem", "digital marketing"],
    "Sales": ["sales", "salesforce", "crm", "business development"],
    "Accounting": ["accounting", "bookkeeping", "quickbooks"],
    "Finance": ["finance", "financial analysis", "financial modeling"],
    "Customer Service": ["customer service", "customer support"],
    "Human Resources": ["human resources", "recruiting", "talent acquisition"],
}

_STOPWORDS = {
    "the", "and", "for", "with", "you", "are", "our", "this", "that", "will",
    "have", "your", "from", "all", "can", "but", "not", "who", "out", "use",
}


def _compile(gazetteer: dict[str, list[str]]) -> list[tuple[str, re.Pattern]]:
    compiled = []
    for canonical, aliases in gazetteer.items():
        parts = []
        for a in aliases:
            # If the alias already contains regex metacharacters keep it,
            # otherwise escape and wrap with word boundaries.
            if any(ch in a for ch in ".\\+#/"):
                parts.append(a)
            else:
                parts.append(r"\b" + re.escape(a) + r"\b")
        compiled.append((canonical, re.compile("|".join(parts), re.IGNORECASE)))
    return compiled


class SkillExtractor:
    """Dictionary + boundary-matching skill extractor."""

    def __init__(self, gazetteer: dict[str, list[str]] | None = None):
        self.gazetteer = gazetteer or SKILL_GAZETTEER
        self._patterns = _compile(self.gazetteer)

    def extract(self, text: str | None) -> list[str]:
        if not text:
            return []
        found = []
        for canonical, pattern in self._patterns:
            if pattern.search(text):
                found.append(canonical)
        return found

    def extract_counts(self, texts: Iterable[str]) -> Counter:
        counter: Counter = Counter()
        for t in texts:
            counter.update(self.extract(t))
        return counter

    @staticmethod
    def tokenize(text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", (text or "").lower())
        return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


# Module-level singleton for convenience.
default_extractor = SkillExtractor()
