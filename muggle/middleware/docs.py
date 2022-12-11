#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from muggle.pages.docs import DocumentLayout
from muggle.pages.guide import GuideLayout


class Docs:

    def __init__(self, guide_uri, docs_uri):
        self.docs_layout = DocumentLayout(docs_uri)
        self.guide_layout = GuideLayout(guide_uri)

