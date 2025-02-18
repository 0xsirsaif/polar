from abc import abstractmethod
from typing import Tuple
from uuid import UUID

from jinja2 import StrictUndefined
from jinja2.nativetypes import NativeEnvironment
from pydantic import BaseModel

from polar.models.user import User


class NotificationBase(BaseModel):
    @abstractmethod
    def subject(self) -> str:
        pass

    @abstractmethod
    def body(self) -> str:
        pass

    def render(
        self,
        user: User,
    ) -> Tuple[str, str]:
        m: dict[str, str] = vars(self)
        m["username"] = user.username

        env = NativeEnvironment(undefined=StrictUndefined)

        subject = env.from_string(self.subject()).render(m).strip()
        body = env.from_string(self.body()).render(m).strip()

        return (subject, body)


class MaintainerPledgeCreatedNotification(NotificationBase):
    pledger_name: str
    pledge_amount: str
    issue_url: str
    issue_title: str
    issue_org_name: str
    issue_repo_name: str
    issue_number: int
    maintainer_has_stripe_account: bool
    pledge_id: UUID | None = None  # Added 2022-06-26

    def subject(self) -> str:
        return "New ${{pledge_amount}} pledge for {{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}"  # noqa: E501

    def body(self) -> str:
        return """Hi,<br><br>

Great news! You received a <strong>${{pledge_amount}}</strong> pledge for: <a href="{{issue_url}}">{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}} - {{issue_title}}</a>.<br><br>

You&apos;ll receive the funds once {{issue_org_name}}/{{issue_repo_name}}#{{issue_number}} is completed and after a 14 day review period.

{% if not maintainer_has_stripe_account -%}
<br><br>Create a Stripe account with Polar today to avoid any delay with future transfers.<br>
<a href="https://polar.sh/maintainer/{{issue_org_name}}/finance">polar.sh/maintainer/{{issue_org_name}}/finance</a>
{% endif -%}
"""  # noqa: E501


class MaintainerPledgeConfirmationPendingNotification(NotificationBase):
    pledger_name: str
    pledge_amount: str
    issue_url: str
    issue_title: str
    issue_org_name: str
    issue_repo_name: str
    issue_number: int
    maintainer_has_stripe_account: bool
    pledge_id: UUID | None = None  # Added 2022-06-26

    def subject(self) -> str:
        return "Please confirm that {{issue_org_name}}/{{issue_repo_name}}#{{issue_number}} is completed"  # noqa: E501

    def body(self) -> str:
        return """Hi,<br><br>

Your backers have pledged ${{pledge_amount}} behind <a href="{{issue_url}}">{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}</a> which which has now been closed.<br><br>

Before you can receive the money, please verify that the issue is completed on <a href="https://polar.sh/maintainer/{{issue_org_name}}/issues">your Polar dashboard</a>.<br><br>

{% if not maintainer_has_stripe_account %}
Create a Stripe account with Polar today to ensure we can transfer the funds directly once the review period is completed.<br>
<a href="https://polar.sh/maintainer/{{issue_org_name}}/finance">polar.sh/maintainer/{{issue_org_name}}/finance</a>
{% endif %}
"""  # noqa: E501


class MaintainerPledgePendingNotification(NotificationBase):
    pledger_name: str
    pledge_amount: str
    issue_url: str
    issue_title: str
    issue_org_name: str
    issue_repo_name: str
    issue_number: int
    maintainer_has_stripe_account: bool
    pledge_id: UUID | None  # Added 2022-06-26

    def subject(self) -> str:
        return "You have ${{pledge_amount}} in pending pledges for {{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}!"  # noqa: E501

    def body(self) -> str:
        return """Hi,<br><br>

Your backers had pledged ${{pledge_amount}} behind <a href="{{issue_url}}">{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}</a> which has now been completed - awesome work!<br><br>

We&apos;ve notified the backers and unless we receive any disputes within the next 14 days it will be transferred to your Stripe account.<br><br>

{% if not maintainer_has_stripe_account %}
Create a Stripe account with Polar today to ensure we can transfer the funds directly once the review period is completed.<br>
<a href="https://polar.sh/maintainer/{{issue_org_name}}/finance">polar.sh/maintainer/{{issue_org_name}}/finance</a>
{% endif %}
"""  # noqa: E501


# No longer sent as of 2023-08-16
class MaintainerPledgePaidNotification(NotificationBase):
    paid_out_amount: str
    issue_url: str
    issue_title: str
    issue_org_name: str
    issue_repo_name: str
    issue_number: int
    pledge_id: UUID | None  # Added 2022-06-26

    def subject(self) -> str:
        return "${{paid_out_amount}} transferred for {{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}"  # noqa: E501

    def body(self) -> str:
        return """Hi,<br><br>

We&apos;ve now transferred ${{paid_out_amount}} in approved pledges for your efforts on <a href="{{issue_url}}">{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}</a>. It will arrive to your Stripe account that you have connected with Polar.<br><br>

Don&apos;t hesitate to reply here with any questions you might have.<br><br>

Best,<br>
Polar

"""  # noqa: E501


class RewardPaidNotification(NotificationBase):
    paid_out_amount: str
    issue_url: str
    issue_title: str
    issue_org_name: str
    issue_repo_name: str
    issue_number: int
    issue_id: UUID
    pledge_id: UUID

    def subject(self) -> str:
        return "${{paid_out_amount}} transferred for {{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}"  # noqa: E501

    def body(self) -> str:
        return """Hi,<br><br>

We&apos;ve now transferred ${{paid_out_amount}} in approved pledges for your efforts on <a href="{{issue_url}}">{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}</a>. It will arrive to the account that you'be connected to Polar.<br><br>

Don&apos;t hesitate to reply here with any questions you might have.<br><br>

Best,<br>
Polar

"""  # noqa: E501


class PledgerPledgePendingNotification(NotificationBase):
    pledge_amount: str
    issue_url: str
    issue_title: str
    issue_number: int
    issue_org_name: str
    issue_repo_name: str
    pledge_date: str
    pledge_id: UUID | None  # Added 2022-06-26

    def subject(self) -> str:
        return "{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}} is completed"

    def body(self) -> str:
        return """Hi,<br><br>

Good news: <a href="{{issue_url}}">{{issue_org_name}}/{{issue_repo_name}}#{{issue_number}}</a> has been completed! You pledged ${{pledge_amount}} behind it on {{pledge_date}}. It will be rewarded to the creators in 14 days unless you file a dispute via email or the Polar dashboard within the next 7 days.
"""  # noqa: E501
