#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
import ast
import csv
import gradio as gr
from pathlib import Path
from typing import Union, List, Dict, Callable, Optional, Any
from gradio import utils
from gradio.context import Context
from gradio.flagging import CSVLogger
from gradio.components import IOComponent
from gradio.documentation import document

gr.helpers.CACHED_FOLDER = ".cached_examples"


@document()
class Examples(gr.helpers.Examples):

    def __init__(
            self,
            examples: List[Any] | List[List[Any]] | str,
            inputs: IOComponent | List[IOComponent],
            outputs: Optional[IOComponent | List[IOComponent]] = None,
            fn: Optional[Callable] = None,
            examples_per_page: int = 10,
            _api_mode: bool = False,
            label: str = "Examples",
            elem_id: Optional[str] = None,
            preprocess: bool = True,
            postprocess: bool = True,
            _initiated_directly: bool = False,
    ):
        super(Examples, self).__init__(
            examples=examples,
            inputs=inputs,
            outputs=outputs,
            fn=fn,
            cache_examples=True,
            examples_per_page=examples_per_page,
            _api_mode=_api_mode,
            label=label,
            elem_id=elem_id,
            preprocess=preprocess,
            postprocess=postprocess,
            _initiated_directly=False
        )

    async def cache(self) -> None:
        """
        Caches all the examples so that their predictions can be shown immediately.
        """
        if not Path(self.cached_file).exists():
            if Context.root_block is None:
                raise ValueError("Cannot cache examples if not in a Blocks context")

            # print(f"Caching examples at: '{utils.abspath(self.cached_folder)}'")
            cache_logger = CSVLogger()

            # create a fake dependency to process the examples and get the predictions
            dependency, fn_index = Context.root_block.set_event_trigger(
                event_name="fake_event",
                fn=self.fn,
                inputs=self.inputs_with_examples,  # type: ignore
                outputs=self.outputs,  # type: ignore
                preprocess=self.preprocess and not self._api_mode,
                postprocess=self.postprocess and not self._api_mode,
                batch=self.batch,
            )

            assert self.outputs is not None
            cache_logger.setup(self.outputs, self.cached_folder)
            for example_id, _ in enumerate(self.examples):
                processed_input = self.processed_examples[example_id]
                if self.batch:
                    processed_input = [[value] for value in processed_input]
                prediction = await Context.root_block.process_api(
                    fn_index=fn_index, inputs=processed_input, request=None, state={}
                )
                output = prediction["data"]
                if self.batch:
                    output = [value[0] for value in output]
                cache_logger.flag(output)
            # Remove the "fake_event" to prevent bugs in loading interfaces from spaces
            Context.root_block.dependencies.remove(dependency)
            Context.root_block.fns.pop(fn_index)