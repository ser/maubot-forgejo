# github - A maubot plugin to act as a GitHub client and webhook receiver.
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Any, Dict, List, NewType, Optional, Type, Union
from datetime import datetime

from attr import dataclass
import attr

from mautrix.types import (
    JSON,
    SerializableAttrs,
    SerializableEnum,
    deserializer,
    serializer,
)

HubDateTime = NewType("HubDateTime", datetime)
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


@serializer(HubDateTime)
def datetime_serializer(dt: HubDateTime) -> JSON:
    return dt.strftime(ISO_FORMAT)


@deserializer(HubDateTime)
def datetime_deserializer(data: JSON) -> HubDateTime:
    if isinstance(data, int):
        return HubDateTime(datetime.utcfromtimestamp(data))
    else:
        return HubDateTime(datetime.strptime(data, ISO_FORMAT))


@dataclass
class User(SerializableAttrs):
    login: str
    id: int
    avatar_url: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    html_url: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    node_id: Optional[str] = None
    gravatar_id: Optional[str] = None
    site_admin: Optional[bool] = None
    followers_url: Optional[str] = None
    following_url: Optional[str] = None
    gists_url: Optional[str] = None
    subscriptions_url: Optional[str] = None
    organizations_url: Optional[str] = None
    repos_url: Optional[str] = None
    events_url: Optional[str] = None
    received_events_url: Optional[str] = None
    name: Optional[str] = None


@dataclass
class Organization(SerializableAttrs):
    id: int
    login: str
    description: str

    url: str
    avatar_url: str
    repos_url: str
    hooks_url: str
    events_url: str

    node_id: Optional[str] = None
    public_members_url: Optional[str] = None
    issues_url: Optional[str] = None


@dataclass
class GitUser(SerializableAttrs):
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None


@dataclass
class License(SerializableAttrs):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: Optional[str] = None


@dataclass
class Repository(SerializableAttrs):
    id: int
    name: str
    full_name: str
    owner: User
    description: Optional[str] = None
    private: Optional[bool] = None
    fork: Optional[bool] = None
    html_url: Optional[str] = None
    created_at: Optional[HubDateTime] = None
    node_id: Optional[str] = None
    forks_url: Optional[str] = None
    keys_url: Optional[str] = None
    collaborators_url: Optional[str] = None
    teams_url: Optional[str] = None
    hooks_url: Optional[str] = None
    issue_events_url: Optional[str] = None
    assignees_url: Optional[str] = None
    branches_url: Optional[str] = None
    tags_url: Optional[str] = None
    blobs_url: Optional[str] = None
    git_tags_url: Optional[str] = None
    git_refs_url: Optional[str] = None
    trees_url: Optional[str] = None
    statuses_url: Optional[str] = None
    languages_url: Optional[str] = None
    stargazers_url: Optional[str] = None
    contributors_url: Optional[str] = None
    subscribers_url: Optional[str] = None
    subscription_url: Optional[str] = None
    commits_url: Optional[str] = None
    git_commits_url: Optional[str] = None
    comments_url: Optional[str] = None
    issue_comment_url: Optional[str] = None
    contents_url: Optional[str] = None
    compare_url: Optional[str] = None
    merges_url: Optional[str] = None
    archive_url: Optional[str] = None
    downloads_url: Optional[str] = None
    issues_url: Optional[str] = None
    pulls_url: Optional[str] = None
    milestones_url: Optional[str] = None
    notifications_url: Optional[str] = None
    labels_url: Optional[str] = None
    releases_url: Optional[str] = None
    deployments_url: Optional[str] = None

    updated_at: Optional[HubDateTime] = None
    pushed_at: Optional[HubDateTime] = None

    git_url: Optional[str] = None
    ssh_url: Optional[str] = None
    clone_url: Optional[str] = None
    svn_url: Optional[str] = None

    homepage: Optional[str] = None
    size: Optional[int] = None
    stargazers_count: Optional[int] = None
    stars_count: Optional[int] = None
    watchers_count: Optional[int] = None
    open_issues_count: Optional[int] = None
    forks_count: Optional[int] = None
    language: Optional[str] = None
    license: Optional[License] = None
    has_issues: Optional[bool] = None
    has_projects: Optional[bool] = None
    has_downloads: Optional[bool] = None
    has_wiki: Optional[bool] = None
    has_pages: Optional[bool] = None
    mirror_url: Optional[str] = None
    archived: Optional[bool] = None
    disabled: Optional[bool] = None
    default_branch: Optional[str] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.full_name,
        }


@dataclass
class Commit(SerializableAttrs):
    id: str
    message: str
    url: str
    author: GitUser
    committer: GitUser
    timestamp: Optional[HubDateTime] = None
    added: List[str] = attr.ib(factory=list)
    removed: List[str] = attr.ib(factory=list)
    modified: List[str] = attr.ib(factory=list)
    tree_id: Optional[str] = None
    distinct: Optional[bool] = None


@dataclass
class PushEvent(SerializableAttrs):
    ref: str
    before: str
    after: str
    repository: Repository
    pusher: GitUser
    sender: User
    commits: List[Commit] = attr.ib(factory=list)
    compare: Optional[str] = None
    created: Optional[bool] = None
    deleted: Optional[bool] = None
    forced: Optional[bool] = None
    base_ref: Optional[str] = None
    head_commit: Optional[Commit] = None
    size: Optional[int] = None
    distinct_size: Optional[int] = None

    @property
    def message_id(self) -> str:
        if not self.head_commit:
            return ""
        return f"push-{self.repository.id}-{self.head_commit.id}"


@dataclass
class ReleaseAsset(SerializableAttrs):
    id: int
    node_id: int
    url: str
    browser_download_url: str
    name: str
    label: str
    state: str
    content_type: str
    size: int
    download_count: str
    created_at: HubDateTime
    uploader: User
    updated_at: Optional[HubDateTime] = None


@dataclass
class Release(SerializableAttrs):
    id: int
    node_id: str
    tag_name: str
    target_commitish: str
    draft: bool
    prerelease: bool
    author: User
    created_at: HubDateTime
    url: str
    assets_url: str
    upload_url: str
    tarball_url: str
    zipball_url: str
    html_url: str
    assets: List[ReleaseAsset]
    body: Optional[str] = None
    published_at: Optional[HubDateTime] = None
    name: Optional[str] = None


class ReleaseAction(SerializableEnum):
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    PRERELEASED = "prereleased"
    RELEASED = "released"


@dataclass
class ReleaseEvent(SerializableAttrs):
    action: ReleaseAction
    release: Release
    repository: Repository
    sender: User


class WatchAction(SerializableEnum):
    STARTED = "started"


@dataclass
class WatchEvent(SerializableAttrs):
    action: WatchAction
    repository: Repository
    sender: User


@dataclass
class ForkEvent(SerializableAttrs):
    forkee: Repository
    repository: Repository
    sender: User


@dataclass
class Label(SerializableAttrs):
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool


class IssueState(SerializableEnum):
    OPEN = "open"
    CLOSED = "closed"


class IssueStateReason(SerializableEnum):
    COMPLETED = "completed"
    NOT_PLANNED = "not_planned"
    DUPLICATE = "duplicate"


@dataclass
class Milestone(SerializableAttrs):
    id: int
    node_id: str
    number: int
    title: str
    description: str
    creator: User
    open_issues: int
    closed_issues: int
    state: IssueState
    created_at: HubDateTime
    url: str
    html_url: str
    labels_url: str
    updated_at: Optional[HubDateTime] = None
    due_on: Optional[HubDateTime] = None
    closed_at: Optional[HubDateTime] = None


@dataclass
class IssuePullURLs(SerializableAttrs):
    diff_url: str
    html_url: str
    patch_url: str
    url: str


@dataclass
class Issue(SerializableAttrs):
    id: int
    number: int
    title: str
    body: str

    user: User
    author_association: str
    labels: List[Label]
    state: IssueState
    created_at: HubDateTime

    state_reason: Optional[IssueStateReason] = None
    locked: bool = False
    milestone: Optional[Milestone] = None

    assignees: List[User] = attr.ib(factory=list)

    comments: Optional[int] = None
    updated_at: Optional[HubDateTime] = None
    closed_at: Optional[HubDateTime] = None

    url: Optional[str] = None
    repository_url: Optional[str] = None
    labels_url: Optional[str] = None
    comments_url: Optional[str] = None
    events_url: Optional[str] = None
    html_url: Optional[str] = None

    node_id: Optional[str] = None
    pull_request: Optional[IssuePullURLs] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
        }


class IssueAction(SerializableEnum):
    OPENED = "opened"
    EDITED = "edited"
    DELETED = "deleted"
    PINNED = "pinned"
    UNPINNED = "unpinned"
    CLOSED = "closed"
    REOPENED = "reopened"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    TRANSFERRED = "transferred"
    MILESTONED = "milestoned"
    DEMILESTONED = "demilestoned"

    X_LABEL_AGGREGATE = "xyz.maubot.issue_label_aggregation"
    X_MILESTONE_CHANGED = "xyz.maubot.issue_milestone_changed"


@dataclass
class Change(SerializableAttrs):
    original: str = attr.ib(metadata={"json": "from"})


@dataclass
class IssueChanges(SerializableAttrs):
    body: Optional[Change] = None
    title: Optional[Change] = None


@dataclass
class IssuesEvent(SerializableAttrs):
    action: IssueAction
    issue: Issue
    repository: Repository
    sender: User
    assignee: Optional[User] = None
    label: Optional[Label] = None
    milestone: Optional[Milestone] = None
    changes: Optional[JSON] = None

    @property
    def issue_id(self) -> int:
        return self.issue.id

    def meta(self) -> Dict[str, Any]:
        return {
            "issue": self.issue.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


@dataclass
class IssueComment(SerializableAttrs):
    id: int
    node_id: int
    url: str
    html_url: str
    body: str
    user: User
    created_at: HubDateTime
    updated_at: Optional[HubDateTime] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
        }


class CommentAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class IssueCommentEvent(SerializableAttrs):
    action: CommentAction
    issue: Issue
    comment: IssueComment
    repository: Repository
    sender: User

    @property
    def issue_id(self) -> int:
        return self.issue.id

    def meta(self) -> Dict[str, Any]:
        return {
            "issue": self.issue.meta(),
            "comment": self.comment.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


@dataclass
class WebhookResponse(SerializableAttrs):
    status: str
    code: Optional[int] = None
    message: Optional[str] = None


@dataclass
class WebhookConfig(SerializableAttrs):
    url: str
    content_type: Optional[str] = None
    secret: Optional[str] = None
    insecure_ssl: Optional[str] = None


@dataclass
class Webhook(SerializableAttrs):
    id: int
    type: str
    active: bool
    events: List[str]
    config: WebhookConfig
    created_at: HubDateTime
    name: Optional[str] = None
    updated_at: Optional[HubDateTime] = None
    url: Optional[str] = None
    test_url: Optional[str] = None
    ping_url: Optional[str] = None
    last_response: Optional[WebhookResponse] = None


@dataclass
class PingEvent(SerializableAttrs):
    zen: str
    hook_id: int
    hook: Webhook


@dataclass
class CreateEvent(SerializableAttrs):
    ref_type: str
    ref: str
    master_branch: str
    pusher_type: str
    repository: Repository
    sender: User
    description: Optional[str] = None


@dataclass
class DeleteEvent(SerializableAttrs):
    ref_type: str
    ref: str
    pusher_type: str
    repository: Repository
    sender: User


class MetaAction(SerializableEnum):
    DELETED = "deleted"


@dataclass
class MetaEvent(SerializableAttrs):
    action: MetaAction
    hook: Webhook
    hook_id: int
    repository: Repository
    sender: User


@dataclass
class CommitComment(SerializableAttrs):
    id: int
    node_id: str
    user: User
    url: str
    html_url: str

    body: str
    author_association: str
    commit_id: str
    created_at: HubDateTime
    position: Optional[int] = None
    line: Optional[int] = None
    path: Optional[str] = None
    updated_at: Optional[HubDateTime] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "commit_id": self.commit_id,
        }


@dataclass
class CommitCommentEvent(SerializableAttrs):
    action: CommentAction
    comment: CommitComment
    repository: Repository
    sender: User

    def meta(self) -> Dict[str, Any]:
        return {
            "comment": self.comment.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


@dataclass
class MilestoneChanges(SerializableAttrs):
    title: Optional[Change] = None
    description: Optional[Change] = None
    due_on: Optional[Change] = None


class MilestoneAction(SerializableEnum):
    CREATED = "created"
    OPENED = "opened"
    EDITED = "edited"
    CLOSED = "closed"
    DELETED = "deleted"


@dataclass
class MilestoneEvent(SerializableAttrs):
    action: MilestoneAction
    milestone: Milestone
    repository: Repository
    sender: User
    changes: Optional[IssueChanges] = None


class LabelAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class LabelChanges(SerializableAttrs):
    name: Optional[Change] = None
    color: Optional[Change] = None


@dataclass
class LabelEvent(SerializableAttrs):
    action: LabelAction
    label: Label
    changes: LabelChanges
    repository: Repository
    sender: User


class WikiPageAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"


@dataclass
class WikiPageEvent(SerializableAttrs):
    action: WikiPageAction
    page_name: str
    title: str
    sha: str
    html_url: str
    summary: Optional[str] = None


@dataclass
class WikiEvent(SerializableAttrs):
    pages: List[WikiPageEvent]
    repository: Repository
    sender: User


@dataclass
class PublicEvent(SerializableAttrs):
    repository: Repository
    sender: User


class PullRequestState(SerializableEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class PullRequestRef(SerializableAttrs):
    label: str
    ref: str
    sha: str
    user: User
    repo: Repository


class TeamPrivacy(SerializableEnum):
    SECRET = "secret"
    CLOSED = "closed"


class TeamPermission(SerializableEnum):
    PULL = "pull"
    PUSH = "push"
    ADMIN = "admin"


@dataclass
class Team(SerializableAttrs):
    id: int
    node_id: str
    name: str
    slug: str
    description: str
    privacy: TeamPrivacy
    permission: TeamPermission

    url: str
    html_url: str
    members_url: str
    repositories_url: str


@dataclass
class PartialPullRequest(SerializableAttrs):
    id: int
    number: int
    state: PullRequestState
    locked: bool
    title: str
    body: str
    user: User

    labels: List[Label]
    assignees: List[User]
    requested_reviewers: List[User]
    requested_teams: List[Team]

    author_association: str
    merge_commit_sha: str

    head: PullRequestRef
    base: PullRequestRef

    created_at: HubDateTime
    html_url: str

    milestone: Optional[Milestone] = None
    updated_at: Optional[HubDateTime] = None
    closed_at: Optional[HubDateTime] = None
    merged_at: Optional[HubDateTime] = None

    diff_url: Optional[str] = None
    patch_url: Optional[str] = None
    issue_url: Optional[str] = None
    commits_url: Optional[str] = None
    review_comments_url: Optional[str] = None
    review_comment_url: Optional[str] = None
    comments_url: Optional[str] = None
    statuses_url: Optional[str] = None

    node_id: Optional[str] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
        }


@dataclass
class PullRequest(PartialPullRequest, SerializableAttrs):
    merged_by: Optional[User] = None

    draft: bool = False
    merged: bool = False
    mergeable: bool = True
    rebaseable: bool = True
    mergeable_state: str = ""

    comments: int = 0
    review_comments: int = 0
    maintainer_can_modify: bool = False
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class PullRequestAction(SerializableEnum):
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_REQUEST_REMOVED = "review_request_removed"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    OPENED = "opened"
    EDITED = "edited"
    CLOSED = "closed"
    REOPENED = "reopened"
    SYNCHRONIZE = "synchronize"
    READY_FOR_REVIEW = "ready_for_review"
    LOCKED = "locked"
    UNLOCKED = "unlocked"

    X_LABEL_AGGREGATE = "xyz.maubot.pr_label_aggregation"


@dataclass
class PullRequestEvent(SerializableAttrs):
    action: PullRequestAction
    pull_request: PullRequest
    number: int
    repository: Repository
    sender: User
    changes: Optional[IssueChanges] = None
    label: Optional[Label] = None
    assignee: Optional[User] = None
    milestone: Optional[Milestone] = None
    requested_reviewer: Optional[User] = None

    @property
    def issue_id(self) -> int:
        return self.pull_request.id

    def meta(self) -> Dict[str, Any]:
        return {
            "pull_request": self.pull_request.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


class PullRequestReviewAction(SerializableEnum):
    SUBMITTED = "submitted"
    EDITED = "edited"
    DISMISSED = "dismissed"


class ReviewState(SerializableEnum):
    COMMENTED = "commented"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"

    @property
    def action_str(self) -> str:
        if self == ReviewState.CHANGES_REQUESTED:
            return "requested changes on"
        elif self == ReviewState.COMMENTED:
            return "commented on"
        else:
            return self.value


@dataclass
class Review(SerializableAttrs):
    id: int
    node_id: str
    user: User
    commit_id: str
    submitted_at: HubDateTime
    state: ReviewState
    html_url: str
    pull_request_url: str
    author_association: str
    body: Optional[str] = None


@dataclass
class ReviewChanges(SerializableAttrs):
    body: Optional[Change] = None


@dataclass
class PullRequestReviewEvent(SerializableAttrs):
    action: PullRequestReviewAction
    pull_request: PartialPullRequest
    review: Review
    repository: Repository
    sender: User
    changes: Optional[ReviewChanges] = None


class PullRequestReviewCommentAction(SerializableEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"


@dataclass
class ReviewComment(SerializableAttrs):
    id: int
    node_id: str
    pull_request_review_id: int
    user: User
    url: str
    html_url: str

    body: str
    author_association: str
    commit_id: str
    original_commit_id: str
    diff_hunk: str
    position: int
    original_position: int
    path: str

    created_at: HubDateTime
    updated_at: Optional[HubDateTime] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "pull_request_review_id": self.pull_request_review_id,
            "commit_id": self.commit_id,
        }


@dataclass
class PullRequestReviewCommentEvent(SerializableAttrs):
    action: PullRequestReviewCommentAction
    pull_request: PartialPullRequest
    comment: ReviewComment
    repository: Repository
    sender: User
    changes: Optional[ReviewChanges] = None

    def meta(self) -> Dict[str, Any]:
        return {
            "pull_request": self.pull_request.meta(),
            "comment": self.comment.meta(),
            "repository": self.repository.meta(),
            "action": str(self.action),
        }


class RepositoryAction(SerializableEnum):
    CREATED = "created"
    DELETED = "deleted"
    ARCHIVED = "archived"
    UNARCHIVED = "unarchived"
    EDITED = "edited"
    RENAMED = "renamed"
    TRANSFERRED = "transferred"
    PUBLICIZED = "publicized"
    PRIVATIZED = "privatized"


@dataclass
class RepositoryEvent(SerializableAttrs):
    action: RepositoryAction
    repository: Repository
    sender: User

    organization: Optional[Organization] = None
    user: Optional[User] = None
    changes: Optional[JSON] = None


class WorkflowJobAction(SerializableEnum):
    QUEUED = "queued"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WorkflowConclusion(SerializableEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    STALE = "stale"
    SKIPPED = "skipped"


@dataclass
class WorkflowJob(SerializableAttrs):
    id: int
    run_id: int
    run_url: str
    name: str
    head_sha: str
    conclusion: Optional[WorkflowConclusion] = None

    @property
    def meta(self) -> JSON:
        info = {
            "id": self.id,
            "run_id": self.run_id,
            "name": self.name,
            "url": self.run_url,
        }
        if self.conclusion:
            info["conclusion"] = self.conclusion.name
        return info


_build_status_circles: Dict[
    WorkflowJobAction, Union[Dict[WorkflowConclusion, str], str]
] = {
    WorkflowJobAction.QUEUED: "🟡",
    WorkflowJobAction.WAITING: "🟠",
    WorkflowJobAction.IN_PROGRESS: "🔵",
    WorkflowJobAction.COMPLETED: {
        WorkflowConclusion.SUCCESS: "🟢",
        WorkflowConclusion.FAILURE: "🔴",
        WorkflowConclusion.NEUTRAL: "⚪",
        WorkflowConclusion.CANCELLED: "⚫️",
        WorkflowConclusion.TIMED_OUT: "⏱️",
        WorkflowConclusion.ACTION_REQUIRED: "⚠️",
        WorkflowConclusion.STALE: "⚪",
        WorkflowConclusion.SKIPPED: "⏩️",
    },
}


@dataclass
class WorkflowJobEvent(SerializableAttrs):
    action: WorkflowJobAction
    workflow_job: WorkflowJob
    repository: Repository
    sender: User

    organization: Optional[Organization] = None

    @property
    def push_id(self) -> str:
        return f"push-{self.repository.id}-{self.workflow_job.head_sha}"

    @property
    def reaction_id(self) -> str:
        return f"job-{self.repository.id}-{self.workflow_job.head_sha}-{self.workflow_job.id}"

    @property
    def color_circle(self) -> str:
        circle_def = _build_status_circles[self.action]
        if isinstance(circle_def, str):
            return circle_def
        else:
            return circle_def[self.workflow_job.conclusion]

    @property
    def meta(self) -> JSON:
        return {"build": self.workflow_job.meta}


class EventType(SerializableEnum):
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PUSH = "push"
    RELEASE = "release"
    WATCH = "watch"
    PING = "ping"
    FORK = "fork"
    CREATE = "create"
    DELETE = "delete"
    META = "meta"
    COMMIT_COMMENT = "commit_comment"
    MILESTONE = "milestone"
    LABEL = "label"
    WIKI = "gollum"
    PUBLIC = "public"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    REPOSITORY = "repository"
    WORKFLOW_JOB = "workflow_job"


Event = Union[
    IssuesEvent,
    IssueCommentEvent,
    PushEvent,
    ReleaseEvent,
    WatchEvent,
    PingEvent,
    ForkEvent,
    CreateEvent,
    MetaEvent,
    CommitCommentEvent,
    MilestoneEvent,
    LabelEvent,
    WikiEvent,
    PublicEvent,
    PullRequestEvent,
    PullRequestReviewEvent,
    PullRequestReviewCommentEvent,
    RepositoryEvent,
    DeleteEvent,
    WorkflowJobEvent,
]

Action = Union[
    IssueAction,
    CommentAction,
    WikiPageAction,
    MetaAction,
    ReleaseAction,
    PullRequestAction,
    PullRequestReviewAction,
    PullRequestReviewCommentAction,
    MilestoneAction,
    LabelAction,
    RepositoryAction,
    WorkflowJobAction,
]

EVENT_CLASSES = {
    EventType.ISSUES: IssuesEvent,
    EventType.ISSUE_COMMENT: IssueCommentEvent,
    EventType.PUSH: PushEvent,
    EventType.RELEASE: ReleaseEvent,
    EventType.WATCH: WatchEvent,
    EventType.PING: PingEvent,
    EventType.FORK: ForkEvent,
    EventType.CREATE: CreateEvent,
    EventType.DELETE: DeleteEvent,
    EventType.META: MetaEvent,
    EventType.COMMIT_COMMENT: CommitCommentEvent,
    EventType.MILESTONE: MilestoneEvent,
    EventType.LABEL: LabelEvent,
    EventType.WIKI: WikiEvent,
    EventType.PUBLIC: PublicEvent,
    EventType.PULL_REQUEST: PullRequestEvent,
    EventType.PULL_REQUEST_REVIEW: PullRequestReviewEvent,
    EventType.PULL_REQUEST_REVIEW_COMMENT: PullRequestReviewCommentEvent,
    EventType.REPOSITORY: RepositoryEvent,
    EventType.WORKFLOW_JOB: WorkflowJobEvent,
}


def expand_enum(enum: Type[SerializableEnum]) -> Dict[str, SerializableEnum]:
    if not enum:
        return {}
    return {field.name: field for field in enum}


ACTION_CLASSES = {
    EventType.ISSUES: IssueAction,
    EventType.COMMIT_COMMENT: CommentAction,
    EventType.ISSUE_COMMENT: CommentAction,
    EventType.PULL_REQUEST: PullRequestAction,
    EventType.PULL_REQUEST_REVIEW: PullRequestReviewAction,
    EventType.PULL_REQUEST_REVIEW_COMMENT: PullRequestReviewCommentAction,
    EventType.WIKI: WikiPageAction,
    EventType.META: MetaAction,
    EventType.RELEASE: ReleaseAction,
    EventType.MILESTONE: MilestoneAction,
    EventType.LABEL: LabelAction,
    EventType.REPOSITORY: RepositoryAction,
    EventType.WORKFLOW_JOB: WorkflowJobAction,
}

OTHER_ENUMS = {
    "ReviewState": ReviewState,
}
