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

import itertools
import tempfile
import zipfile
import unicodedata
import re

from bika.lims import _
from bika.lims import api
from bika.lims.browser.workflow import RequestContextAware
from bika.lims.interfaces import IWorkflowActionUIDsAdapter
from bika.lims.workflow import doActionFor
from DateTime import DateTime
from ZODB.POSException import POSKeyError
from zope.interface import implements

try:
    from urllib import quote  # Py2
except ImportError:
    from urllib.parse import quote  # Py3 (ileride uyum için)

def _sanitize_ascii(value):
    """Unicode girdiyi güvenli ASCII dosya adına çevirir."""
    if value is None:
        return u""
    # Py2: 'str' ise UTF-8 varsayalım -> unicode'a çevir
    if isinstance(value, str):
        try:
            value = value.decode('utf-8')
        except Exception:
            value = unicode(value)  # son çare
    # NFKD -> ASCII
    ascii_val = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    ascii_val = ascii_val.decode('ascii')
    # Dosya adı için güvenli karakter seti
    return re.sub(r'[^\w\-_.]', '_', ascii_val)

class WorkflowActionDownloadReportsAdapter(RequestContextAware):
    """Adapter in charge of the client 'publish_samples' action
    """
    implements(IWorkflowActionUIDsAdapter)

    def __call__(self, action, uids):
        # get the selected ARReport objects
        reports = map(api.get_object_by_uid, uids)

        pdfs = []

        for report in reports:
            sample = report.getAnalysisRequest()
            sample_id = api.get_id(sample)

            pdf = self.get_pdf(report)
            if pdf is None:
                self.add_status_message(
                    _("Could not load PDF for sample {}"
                      .format(sample_id)), "warning")
                continue

            # Hasta + test adlarını güvenli hale getir
            patient_full_name = sample.getPatientFullName() or u"HASTA"
            safe_patient = _sanitize_ascii(patient_full_name)

            analyses = sample.getAnalyses(full_objects=True)
            short_titles = [(a.getService().getShortTitle() or "TEST") for a in analyses]
            titles_str = u"_".join(short_titles)
            safe_titles = _sanitize_ascii(titles_str)

            # Tamamı ASCII olacak dosya adı
            pdf.filename = u"{}-{}-{}.pdf".format(sample_id, safe_patient, safe_titles)

            pdfs.append(pdf)

        if len(pdfs) == 1:
            pdf = pdfs[0]
            return self.download(pdf.data, pdf.filename, type="application/pdf")

        with self.create_archive(pdfs) as archive:
            timestamp = DateTime().strftime("%Y%m%d_%H%M%S")
            archive_name = "Reports-{}.zip".format(timestamp)
            data = archive.file.read()
            return self.download(data, archive_name, type="application/zip")

    def create_archive(self, pdfs):
        """Create an ZIP archive with the given PDFs
        """
        archive = tempfile.NamedTemporaryFile(suffix=".zip")
        with zipfile.ZipFile(archive.name, "w", zipfile.ZIP_DEFLATED) as zf:
            for pdf in pdfs:
                zf.writestr(pdf.filename, pdf.data)
        return archive

    def download(self, data, filename, type="application/zip"):
        response = self.request.response

        # Fallback ASCII 'filename=' ve RFC 5987 uyumlu UTF-8 'filename*=' birlikte verilsin
        # (filename ASCII olduğu için güvenli; yine de iki başlık sunmak iyi pratik)
        ascii_name = filename if isinstance(filename, str) else filename.encode('ascii', 'ignore')
        if not isinstance(ascii_name, str):
            ascii_name = ascii_name.decode('ascii')

        utf8_quoted = quote(filename.encode('utf-8') if not isinstance(filename, bytes) else filename)

        cd_value = "attachment; filename=\"{}\"; filename*=UTF-8''{}".format(ascii_name, utf8_quoted)
        response.setHeader("Content-Disposition", cd_value)
        response.setHeader("Content-Type", "{}; charset=utf-8".format(type))
        response.setHeader("Content-Length", len(data))
        response.setHeader("Cache-Control", "no-store")
        response.setHeader("Pragma", "no-cache")
        response.write(data)

    def get_pdf(self, report):
        """Get the report PDF
        """
        try:
            return report.getPdf()
        except (POSKeyError, TypeError):
            return None


class WorkflowActionPublishSamplesAdapter(RequestContextAware):
    """Adapter in charge of the client 'publish_samples' action
    """
    implements(IWorkflowActionUIDsAdapter)

    def __call__(self, action, uids):
        published = []

        # get the selected ARReport objects
        reports = map(api.get_object_by_uid, uids)
        # get all the contained sample UIDs of the generated PDFs
        sample_uids = map(self.get_sample_uids_in_report, reports)
        # uniquify the UIDs of the contained samples
        unique_sample_uids = set(list(
            itertools.chain.from_iterable(sample_uids)))

        # publish all the contained samples of the selected reports
        for uid in unique_sample_uids:
            sample = api.get_object_by_uid(uid)
            if self.publish_sample(sample):
                published.append(sample)

        # generate a status message of the published sample IDs
        message = _("No items published")
        if published:
            message = _("Published {}".format(
                ", ".join(map(api.get_id, published))))

        # add the status message for the response
        self.add_status_message(message, "info")

        # redirect back
        referer = self.request.get_header("referer")
        return self.redirect(redirect_url=referer)

    def get_sample_uids_in_report(self, report):
        """Return a list of contained sample UIDs
        """
        metadata = report.getMetadata() or {}
        return metadata.get("contained_requests", [])

    def publish_sample(self, sample):
        """Set status to prepublished/published/republished
        """
        status = api.get_workflow_status_of(sample)
        transitions = {"verified": "publish", "published": "republish"}
        transition = transitions.get(status, "prepublish")
        succeed, message = doActionFor(sample, transition)
        return succeed
