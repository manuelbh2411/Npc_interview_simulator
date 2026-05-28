from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base  # noqa: E402
from app.models.interview import Interview  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.user import User  # noqa: E402


DEFAULT_SQLITE_PATH = BACKEND_DIR / "app" / "data" / "tfg_interviews.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migra datos desde SQLite local a la DATABASE_URL persistente.",
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SQLITE_PATH),
        help="Ruta del SQLite local. Por defecto usa backend/app/data/tfg_interviews.db.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="URL SQLAlchemy de destino. Ejemplo: postgresql+psycopg://user:pass@host/db",
    )
    parser.add_argument(
        "--clear-target",
        action="store_true",
        help="Borra primero tablas de destino. Usalo solo si la base remota esta dedicada al TFG.",
    )
    return parser.parse_args()


def clone_user(user: User) -> User:
    return User(
        id=user.id,
        name=user.name,
        email=user.email,
        hashed_password=user.hashed_password,
        created_at=user.created_at,
    )


def clone_interview(interview: Interview) -> Interview:
    return Interview(
        id=interview.id,
        session_id=interview.session_id,
        user_id=interview.user_id,
        title=interview.title,
        job_type=interview.job_type,
        personality=interview.personality,
        status=interview.status,
        transcript=interview.transcript,
        report_id=interview.report_id,
        duration_seconds=interview.duration_seconds,
        message_count=interview.message_count,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
        created_at=interview.created_at,
    )


def clone_report(report: Report) -> Report:
    return Report(
        id=report.id,
        interview_id=report.interview_id,
        overall_score=report.overall_score,
        communication_score=report.communication_score,
        coherence_score=report.coherence_score,
        job_fit_score=report.job_fit_score,
        confidence_score=report.confidence_score,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        recommendations=report.recommendations,
        summary_report=report.summary_report,
        final_feedback=report.final_feedback,
        created_at=report.created_at,
    )


def reset_target(db: Session) -> None:
    db.query(Report).delete()
    db.query(Interview).delete()
    db.query(User).delete()
    db.commit()


def sync_postgres_sequences(db: Session) -> None:
    if db.bind is None or db.bind.dialect.name != "postgresql":
        return

    for table_name in ("users", "interviews", "reports"):
        db.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence(:table_name, 'id'),
                    COALESCE((SELECT MAX(id) FROM """ + table_name + """), 1),
                    true
                )
                """
            ),
            {"table_name": table_name},
        )
    db.commit()


def migrate(source_path: Path, target_url: str, clear_target: bool) -> None:
    if not source_path.exists():
        raise SystemExit(f"No existe la base SQLite local: {source_path}")

    source_engine = create_engine(f"sqlite:///{source_path}")
    target_engine = create_engine(target_url, pool_pre_ping=True)
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    Base.metadata.create_all(bind=target_engine)

    with SourceSession() as source, TargetSession() as target:
        users = source.query(User).order_by(User.id).all()
        interviews = source.query(Interview).order_by(Interview.id).all()
        reports = source.query(Report).order_by(Report.id).all()

        if clear_target:
            reset_target(target)

        for user in users:
            target.merge(clone_user(user))
        target.commit()

        for interview in interviews:
            target.merge(clone_interview(interview))
        target.commit()

        for report in reports:
            target.merge(clone_report(report))
        target.commit()

        sync_postgres_sequences(target)

    print("Migracion completada:")
    print(f"- Usuarios: {len(users)}")
    print(f"- Entrevistas: {len(interviews)}")
    print(f"- Informes: {len(reports)}")


if __name__ == "__main__":
    args = parse_args()
    migrate(Path(args.source), args.target, args.clear_target)
