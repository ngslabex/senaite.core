# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.CORE.
#
# SENAITE.CORE is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2018-2024 by it's authors.
# Some rights reserved, see README and LICENSE.

import collections

import six

from bika.lims import api
from bika.lims import senaiteMessageFactory as _
from senaite.app.listing.view import ListingView


class DynamicAnalysisSpecView(ListingView):
    """A listing view that shows the contents of the Excel
    """
    def __init__(self, context, request):
        super(DynamicAnalysisSpecView, self).__init__(context, request)

        self.context_actions = {}
        self.show_search = False
        self.show_column_toggles = False
        self.title = api.get_title(self.context)
        self.description = api.get_description(self.context)

        if self.context.specs_file:
            self.description = "{} {}".format(
                 _(
                    u"dynamic_analysisspec_description",
                    default=u"Contents of the file"
                 ), self.context.specs_file.filename)

        self.specs = self.context.get_specs()
        self.total = len(self.specs)

        self.columns = collections.OrderedDict()
        for title in self.context.get_header():
            self.columns[title] = {
                "title": title,
                "toggle": True}

        self.review_states = [
            {
                "id": "default",
                "title": _(
                    u"listing_dynamic_analysisspec_state_all",
                    default=u"All"
                ),
                "contentFilter": {},
                "transitions": [],
                "custom_transitions": [],
                "columns": self.columns.keys()
            }
        ]

    def make_empty_item(self, record):
        """Create a new empty item
        """
        item = {
            "uid": None,
            "before": {},
            "after": {},
            "replace": {},
            "allow_edit": [],
            "disabled": False,
            "state_class": "state-active",
        }
        for k, v in record.items():
            # ensure keyword dictionary keys contains only strings
            if not self.is_string(k):
                continue
            item[k] = v
        return item

    def is_string(self, value):
        return isinstance(value, six.string_types)

    def folderitems(self):
        items = []
        for record in self.specs:
            items.append(self.make_empty_item(record))
        return items
