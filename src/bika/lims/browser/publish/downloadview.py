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
import unicodedata
import re


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
        """Generate a safe filename for the sample PDF"""
        sample = report.getAnalysisRequest()
        
        # Get patient name - use safe method
        patient_full_name = ""
        try:
            if hasattr(sample, 'getPatientFullName'):
                patient_full_name = sample.getPatientFullName() or "HASTA"
            else:
                patient_full_name = "HASTA"
        except:
            patient_full_name = "HASTA"
        
        # Convert to safe ASCII filename
        safe_patient_name = patient_full_name.encode('ascii', 'ignore').decode('ascii')
        safe_patient_name = re.sub(r'[^\w\-_.]', '_', safe_patient_name)
        
        # Get analysis titles
        analyses = sample.getAnalyses(full_objects=True)
        short_titles = []
        for analysis in analyses:
            service = analysis.getService()
            if service:
                short_title = service.getShortTitle() or "TEST"
                short_titles.append(short_title)
        
        titles_str = "_".join(short_titles)
        safe_titles = titles_str.encode('ascii', 'ignore').decode('ascii')
        safe_titles = re.sub(r'[^\w\-_.]', '_', safe_titles)
        
        return "{}-{}.pdf".format(safe_patient_name, safe_titles)

    def download(self, data, filename, content_type="application/pdf"):
        """Download the PDF
        """
        # Ensure filename is properly encoded for HTTP headers
        if isinstance(filename, unicode):
            filename = filename.encode('utf-8')
        
        self.request.response.setHeader(
            "Content-Disposition", 'inline; filename="{}"'.format(filename))
        self.request.response.setHeader("Content-Type", content_type)
        self.request.response.setHeader("Content-Length", len(data))
        self.request.response.setHeader("Cache-Control", "no-store")
        self.request.response.setHeader("Pragma", "no-cache")
        self.request.response.write(data)