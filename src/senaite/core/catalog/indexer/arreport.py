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

from bika.lims.interfaces import IARReport
from plone.indexer import indexer


@indexer(IARReport)
def sample_uid(instance):
    """Returns a list of UIDs of the contained Samples
    """
    return instance.getRawContainedAnalysisRequests()


@indexer(IARReport)
def arreport_searchable_text(instance):
    sample = instance.getAnalysisRequest()

    tokens = [
        sample.getId(),
    ]

    # Hasta adı
    patient_name = sample.getPatientFullName()
    if patient_name:
        tokens.append(unicode(patient_name, "utf-8") if isinstance(patient_name, str) else patient_name)

    # Test adları
    for analysis in sample.getAnalyses():
        try:
            title = analysis.Title() if callable(analysis.Title) else analysis.Title
            tokens.append(unicode(title, "utf-8") if isinstance(title, str) else title)
        except Exception:
            continue

    return u" ".join(list(set(tokens)))
