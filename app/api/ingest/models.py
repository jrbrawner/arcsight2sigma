from typing import Optional

from sqlmodel import Field

from app.database import BaseModel


class SigmaBase(BaseModel):
    """Base model for Sigma rules"""

    title: str = Field(nullable=False, unique=True)
    rule_id: str = Field(unique=True)
    status: str = Field()
    description: str = Field()
    author: str = Field()
    logsource: str = Field()
    detection: str = Field()
    condition: str = Field()


class SigmaRule(SigmaBase):
    """Database model for SigmaRule."""

    __tablename__ = "SigmaRule"

    id: int = Field(primary_key=True)


class ArcSightBase(BaseModel):
    """Base model for ArcSight rules."""

    name: str = Field(unique=True)
    description: Optional[str] = Field(nullable=True)
    raw: str = Field()
    logic: str = Field()


class ArcSightRuleXML(ArcSightBase, table=True):
    """Database model for ArcSight Rule"""

    __tablename__ = "ArcSightRuleXML"
    id: Optional[int] = Field(default=None, primary_key=True)

    def get_by_name(name):
        return ArcSightRuleXML.query().filter(ArcSightRuleXML.name == name).first()
