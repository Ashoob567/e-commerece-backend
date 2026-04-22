from .base import *
import dj_database_url
import os
from dotenv import load_dotenv

load_dotenv()  # ✅ This line is critical

DEBUG = True

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
    )
}