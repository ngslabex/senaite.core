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
# Copyright 2018-2025 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api
from Products.Five.browser import BrowserView


class DownloadView(BrowserView):
    """Download View
    """

    def __init__(self, context, request):
        super(DownloadView, self).__init__(context, request)

    def __call__(self):
        filename = self.get_report_filename(self.context)
        pdf = self.context.getPdf()
        return self.download(pdf.data, filename)

    def get_report_filename(self, report):
        """Generate the filename for the sample PDF
        """
        sample = report.getAnalysisRequest()
         # Fetch the patient full name
        patient_full_name = sample.getPatientFullName()  # Ensure this method is correct
        # Replace spaces or problematic characters in the patient name
        safe_patient_name = patient_full_name.replace(" ", "_").replace("/", "_")
        # Fetch all analyses and their ShortTitle values
        analyses = sample.getAnalyses(full_objects=True)
         #    short_titles = sample.getShortTitle(full_objects=True)
        short_titles = [
            analysis.getService().getShortTitle() or "TEST"
            for analysis in analyses
        ]
        # Concatenate ShortTitles with a separator (e.g., underscore)
        short_titles_str = "_".join(short_titles)

        # Combine sample ID and patient name
        return "{}-{}-{}.pdf".format(api.get_id(sample), safe_patient_name, short_titles_str)

    def download(self, data, filename, content_type="application/pdf"):
        """Download the PDF
        """
        self.request.response.setHeader(
            "Content-Disposition", 'inline; filename="{}"'.format(filename))
        self.request.response.setHeader("Content-Type", content_type, "application/pdf")
        self.request.response.setHeader("Content-Length", len(data))
        self.request.response.setHeader("Cache-Control", "no-store")
        self.request.response.setHeader("Pragma", "no-cache")
        self.request.response.write(data)
