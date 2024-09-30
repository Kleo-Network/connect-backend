import os

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DB_RESULT_DATE_TIME_FORMAT = "%Y-%m-%dT%H: %M: %S"

AWS_ACCESS_KEY_ID = os.environ.get("API_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")

ACTIVITIES = [
    "Politics",
    "Comedy",
    "Sports",
    "Movies",
    "Reading",
    "Coding",
    "Programming",
    "Designing",
    "Trading",
    "Gaming",
    "Shopping",
    "Podcasts",
    "Music",
    "Medicine",
    "Government",
    "Planning",
    "Job Hunting",
    "Marketplace",
    "Sitcoms",
    "TV Series",
]
