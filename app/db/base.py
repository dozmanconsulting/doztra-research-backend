# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base
from app.models.user import User, Subscription, RefreshToken
from app.models.research_project import ResearchProject
from app.models.generated_content import GeneratedContent
from app.models.content_feedback import ContentFeedback
from app.models.job_application import JobApplication
