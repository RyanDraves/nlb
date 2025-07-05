"""Expression policy to add groups to a user when they are invited to Authentik"""

# https://unhexium.net/authentik/authentik-group-assignment-on-invitation-usage/
from authentik.core.models import Group

if 'prompt_data' not in request.context:
    ak_logger.warn(f'prompt_data not found in {request.context}')
    return True

if 'groups_to_add' not in request.context['prompt_data']:
    ak_logger.info(f'prompt_data does not have any groups to add')
    return True

add_groups = []
for invite_group_name in request.context['prompt_data']['groups_to_add']:
    group = Group.objects.get(name=invite_group_name)
    add_groups.append(group)
    ak_logger.info(f'added {invite_group_name} to user')

# ["groups"] *must* be set to an array of Group objects, names alone are not enough.
request.context['flow_plan'].context['groups'] = add_groups

return True
