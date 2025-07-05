import datetime
import json
from typing import Any, Literal, TypedDict, Unpack

import requests

from nlb.util import secrets


class InvitationCreateRequest(TypedDict):
    name: str
    expires: str
    fixed_data: dict[str, Any]
    single_use: bool
    flow: str


class InvitationCreateResponse(TypedDict):
    pk: str
    name: str
    expires: str
    fixed_data: dict[str, Any]
    created_by: dict[str, Any]
    single_use: bool
    flow: str
    flow_ob: dict[str, Any]


class FlowQuery(TypedDict, total=False):
    denied_action: Literal['continue', 'message', 'message_continue']
    designation: Literal[
        'authentication',
        'authorization',
        'enrollment',
        'invalidation',
        'recovery',
        'stage_configuration',
        'unenrollment',
    ]
    flow_uuid: str
    name: str
    ordering: str
    page: int
    page_size: int
    search: str
    slug: str


class Pagination(TypedDict):
    next: int
    previous: int
    count: int
    current: int
    total_pages: int
    start_index: int
    end_index: int


class Flow(TypedDict):
    pk: str
    policybindingmodel_ptr_id: int
    name: str
    slug: str
    title: str
    designation: Literal[
        'authentication',
        'authorization',
        'enrollment',
        'invalidation',
        'recovery',
        'stage_configuration',
        'unenrollment',
    ]
    background: str
    stages: list[int]
    policies: list[int]
    cache_count: int
    policy_engine_mode: Literal['all', 'any']
    compatibility_mode: bool
    export_url: str
    layout: Literal[
        'stacked', 'content_left', 'content_right', 'sidebar_left', 'sidebar_right'
    ]
    denied_action: Literal['message_continue', 'message', 'continue']
    authentication: Literal[
        'none',
        'required_authenticated',
        'required_unauthenticated',
        'require_superuser',
        'require_redirect',
        'require_outpost',
    ]


class FlowQueryResponse(TypedDict):
    pagination: Pagination
    results: list[Flow]


class GroupQuery(TypedDict, total=False):
    attributes: str
    include_users: bool
    is_superuser: bool
    members_by_pk: list[int]
    members_by_username: list[str]
    name: str
    ordering: str
    page: int
    page_size: int
    search: str


class Group(TypedDict):
    pk: str
    num_pk: int
    name: str
    is_superuser: bool
    parent: str | None
    parent_name: str | None
    users: list[int]
    users_obj: list[dict[str, Any]]
    attributes: dict[str, Any]
    roles: list[str]
    roles_obj: list[dict[str, Any]]


class GroupQueryResponse(TypedDict):
    pagination: Pagination
    results: list[Group]


class AuthentikClient:
    def __init__(self, base_url: str = 'https://authentik.barn-arcturus.ts.net'):
        self._base_url = base_url
        self._headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {secrets.get_secret("authentik.token")}',
        }

    def list_flows(self, **params: Unpack[FlowQuery]) -> FlowQueryResponse:
        url = f'{self._base_url}/api/v3/flows/instances/'

        # Filter out None values
        query_params: dict[str, Any] = {
            k: v for k, v in params.items() if v is not None
        }

        response = requests.get(url, headers=self._headers, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_groups(self, **params: Unpack[GroupQuery]) -> GroupQueryResponse:
        url = f'{self._base_url}/api/v3/core/groups/'

        # Filter out None values
        query_params: dict[str, Any] = {
            k: v for k, v in params.items() if v is not None
        }

        response = requests.get(url, headers=self._headers, params=query_params)
        response.raise_for_status()
        return response.json()

    def invitation_create(
        self,
        name: str,
        flow: str,
        expires: datetime.datetime | None = None,
        fixed_data: dict[str, Any] | None = None,
        single_use: bool = True,
    ) -> str:
        """Create an invitation in Authentik"""
        # Find the requested flow
        flows = self.list_flows(slug=flow)['results']

        # Error check the queried flow
        if not flows:
            raise ValueError(f'No flow found for {flow}')
        if len(flows) > 1:
            raise ValueError(f'Multiple flows found for {flow}: {flows}')
        request_flow = flows[0]
        if request_flow['designation'] != 'enrollment':
            raise ValueError(
                f'Flow {request_flow["name"]} is not an enrollment flow, '
                f'but a {request_flow["designation"]} flow.'
            )

        url = f'{self._base_url}/api/v3/stages/invitation/invitations/'
        if expires is None:
            expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                hours=1
            )

        data: InvitationCreateRequest = {
            'name': name,
            'expires': expires.isoformat(),
            'fixed_data': fixed_data or {},
            'single_use': single_use,
            'flow': request_flow['pk'],
        }
        response = requests.post(url, headers=self._headers, data=json.dumps(data))
        response.raise_for_status()
        resp: InvitationCreateResponse = response.json()

        invite_url = (
            self._base_url + f'/if/flow/{request_flow["slug"]}/?itoken={resp["pk"]}'
        )
        return invite_url
