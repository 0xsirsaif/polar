from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from polar.enums import Platforms
from polar.kit.db.models import RecordModel
from polar.kit.extensions.sqlalchemy import PostgresUUID, StringEnum

if TYPE_CHECKING:  # pragma: no cover
    from polar.models.organization import Organization
    from polar.models.user_organization import UserOrganization


class OAuthAccount(RecordModel):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "account_id",
        ),
    )

    platform: Mapped[Platforms] = mapped_column(StringEnum(Platforms), nullable=False)
    access_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    expires_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    account_id: Mapped[str] = mapped_column(String(320), nullable=False)
    account_email: Mapped[str] = mapped_column(String(320), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID,
        ForeignKey("users.id", ondelete="cascade"),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")


class User(RecordModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    profile: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, default={}, nullable=True
    )

    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        OAuthAccount, lazy="joined", back_populates="user"
    )

    invite_only_approved: Mapped[bool] = mapped_column(Boolean, nullable=False)

    accepted_terms_of_service: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    last_seen_at_extension: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    last_version_extension: Mapped[str] = mapped_column(String(50), nullable=True)

    email_newsletters_and_changelogs: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    email_promotions_and_events: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    __mutables__ = {
        "email",
        "profile",
        "invite_only_approved",
        "accepted_terms_of_service",
    }

    def get_platform_oauth_account(self, platform: Platforms) -> OAuthAccount | None:
        return next(
            (
                account
                for account in self.oauth_accounts
                if account.platform == platform
            ),
            None,
        )
