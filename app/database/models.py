from database.db_config import Base
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class S2Papers(Base):
    __tablename__ = "s2_papers"

    paper_id: Mapped[str] = mapped_column(String, primary_key=True)
    doi_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    arxiv_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    abstract: Mapped[str] = mapped_column(String, nullable=True)
    authors: Mapped[str] = mapped_column(String, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=True)
    open_access_url: Mapped[str] = mapped_column(String, nullable=True)
    journal: Mapped[str] = mapped_column(String, nullable=True)

    # Process Tracking Flags
    is_downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    is_extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    text_data: Mapped["PaperText"] = relationship(
        "PaperText", back_populates="paper", cascade="all, delete-orphan", uselist=False
    )


class PaperText(Base):
    __tablename__ = "paper_texts"

    paper_id: Mapped[str] = mapped_column(
        String, ForeignKey("s2_papers.paper_id", ondelete="CASCADE"), primary_key=True
    )
    full_text: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    paper: Mapped["S2Papers"] = relationship("S2Papers", back_populates="text_data")
