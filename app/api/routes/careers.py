from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from app.db.session import get_db
from app.models.job_application import JobApplication
from app.schemas.careers import JobApplicationCreate, JobApplicationResponse
from app.utils.email import send_email

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/careers/apply", response_model=JobApplicationResponse)
async def apply_for_job(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    linkedin: Optional[str] = Form(None),
    portfolio: Optional[str] = Form(None),
    cover_letter: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Accept job applications, persist to DB, and send an email notification."""
    try:
        # Save optional resume to uploads/ (path only; storage service could be integrated later)
        resume_path = None
        if resume is not None and resume.filename:
            # Basic local save under uploads/job_applications
            from pathlib import Path
            import aiofiles

            target_dir = Path("uploads/job_applications")
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{resume.filename}"
            async with aiofiles.open(file_path, "wb") as f:
                content = await resume.read()
                await f.write(content)
            resume_path = str(file_path)

        # Persist application
        application = JobApplication(
            name=name,
            email=email,
            role=role,
            linkedin=linkedin,
            portfolio=portfolio,
            cover_letter=cover_letter,
            resume_path=resume_path,
            status="submitted",
            metadata={}
        )
        db.add(application)
        db.commit()
        db.refresh(application)

        # Send notification email to hiring inbox
        subject = f"New Job Application: {role} — {name}"
        html_content = f"""
        <h2>New Job Application</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Role:</strong> {role}</p>
        <p><strong>LinkedIn:</strong> {linkedin or '-'}<br/>
        <strong>Portfolio:</strong> {portfolio or '-'}</p>
        <p><strong>Cover letter:</strong><br/>{(cover_letter or '').replace('\n','<br/>')}</p>
        <p><strong>Resume path:</strong> {resume_path or '(none)'}</p>
        <hr/>
        <p>Submitted at: {datetime.utcnow().isoformat()} UTC</p>
        """
        text_content = (
            f"New Job Application\n\nName: {name}\nEmail: {email}\nRole: {role}\n"
            f"LinkedIn: {linkedin or '-'}\nPortfolio: {portfolio or '-'}\n"
            f"Resume: {resume_path or '(none)'}\n\nCover letter:\n{cover_letter or ''}\n"
        )
        # Change to your hiring mailbox
        send_email(
            email_to="info@doztra.co.uk",
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

        return JobApplicationResponse(
            id=str(application.id),
            success=True,
            message="Thanks for applying — we’ve received your application and will get back to you within a few days if it’s a match.",
            created_at=application.created_at,
        )
    except Exception as e:
        logger.error(f"Job application failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit application")
