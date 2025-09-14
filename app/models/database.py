from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    content = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    features = relationship("Feature", back_populates="document", cascade="all, delete-orphan")

class Feature(Base):
    __tablename__ = "features"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"))
    title = Column(String(255), nullable=False)
    user_stories = Column(Text)
    acceptance_criteria = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="features")
    scenarios = relationship("Scenario", back_populates="feature", cascade="all, delete-orphan")

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_id = Column(String, ForeignKey("features.id"))
    content = Column(Text, nullable=False)
    test_type = Column(String(50), default="unit")
    generated_by = Column(String(50), nullable=True)  # 'grok' or 'claude'
    llm_model = Column(String(100), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    token_count = Column(JSON, nullable=True)  # JSON object for input/output tokens
    cost_usd = Column(Float, nullable=True)  # Cost in USD
    prompt_template_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    generation_error = Column(Text, nullable=True)

    # Relationships
    feature = relationship("Feature", back_populates="scenarios")
