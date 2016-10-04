# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

REQUEST=context.REQUEST
membership_tool=context.portal_membership
groups_tool=context.portal_groups
member = membership_tool.getAuthenticatedMember()

member_groups = [groups_tool.getGroupById(group.id).getGroupName() 
                 for group in groups_tool.getGroupsByUserId(member.id)]

for obj in context.clients.objectValues():
    if member.id in obj.users_with_local_role('Owner'):
        dest = obj.absolute_url()
        REQUEST.RESPONSE.redirect(dest)
