from db_config import Base
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class S2Papers(Base):
    __tablename__ = "s2_papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    doi_id:Mapped[str] = mapped_column(String, unique=True, nullable=True)
    arxiv_id:Mapped[str] = mapped_column(String, unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    abstract: Mapped[str] = mapped_column(String, nullable=True)
    authors: Mapped[str] = mapped_column(String, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=True)
    open_access_url:Mapped[str] = mapped_column(String,nullable=True)
    journal:Mapped[str] = mapped_column(String, nullable=True)