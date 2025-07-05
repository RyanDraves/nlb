"""CLI tool for generating invites to authenticated services"""

import datetime

import rich_click as click
from InquirerPy.prompts import input as input_prompt
from InquirerPy.prompts import list as list_prompt

from nlb.authentik import client
from nlb.util import console_utils


def _who_is_it_for() -> str:
    """Prompt the user for the name of the person to invite"""
    return input_prompt.InputPrompt(
        message='Who is this invite for?',
        validate=lambda x: bool(x.strip()),
        default='',
    ).execute()


def _when_to_expire() -> datetime.datetime:
    """Prompt the user for when the invite should expire"""
    options = [
        '1 hour',
        '1 day',
        '1 week',
    ]
    expiration = list_prompt.ListPrompt(
        message='When should this invite expire?',
        choices=options,
        default='1 hour',
    ).execute()
    # Convert the response to a datetime object
    if expiration == '1 hour':
        return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            hours=1
        )
    elif expiration == '1 day':
        return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    elif expiration == '1 week':
        return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            weeks=1
        )

    raise ValueError(f'Unknown expiration option: {expiration}')


def _groups_to_add(c: client.AuthentikClient) -> list[str]:
    groups = c.list_groups(
        is_superuser=False,  # Don't include superuser groups
        include_users=False,
        page_size=30,
    )['results']

    group_names = set(group['name'] for group in groups)
    groups_to_ignore: set[str] = {
        'Invited',  # Added by default
        'authentik Read-only',
        'authentik Admins',
        'Mealie Admins',
    }
    group_names -= groups_to_ignore

    if not group_names:
        return []

    selected_groups = list_prompt.ListPrompt(
        message='Select groups to add the user to:',
        choices=sorted(group_names),
        multiselect=True,
    ).execute()
    return selected_groups


@click.command()
def main() -> None:
    """Invite friends to self-hosted, authenticated services"""
    c = client.AuthentikClient()
    invitation_url = c.invitation_create(
        name=f'invite-for-{_who_is_it_for()}',
        flow='default-enrollment-flow',
        expires=_when_to_expire(),
        fixed_data={
            'groups_to_add': _groups_to_add(c),
        },
        single_use=True,
    )
    console_utils.Console().success(f'Invitation created: {invitation_url}')


if __name__ == '__main__':
    main(prog_name='nlb_invite')
