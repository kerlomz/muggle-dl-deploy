#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from __future__ import annotations
import ast
import csv
import gradio as gr
from typing import Union, List, Dict, Callable, Optional, Any
from gradio import utils
from gradio.context import Context
from gradio.flagging import CSVLogger
from gradio.components import IOComponent
from gradio.documentation import document

gr.examples.CACHED_FOLDER = ".cached_examples"


@document()
class Examples(gr.examples.Examples):

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

    async def load_from_cache(self, example_id: int) -> List[Any]:
        with open(self.cached_file, encoding="utf8") as cache:
            examples = list(csv.reader(cache))
        example = examples[example_id + 1]  # +1 to adjust for header
        output = []
        for component, value in zip(self.outputs, example):
            try:
                value_as_dict = ast.literal_eval(value)
                assert utils.is_update(value_as_dict)
                output.append(value_as_dict)
            except (ValueError, TypeError, SyntaxError, AssertionError):
                output.append(component.serialize(value, self.cached_folder))
        return output

    async def create(self) -> None:

        async def load_example(example_id):
            processed_example = self.non_none_processed_examples[
                                    example_id
                                ] + await self.load_from_cache(example_id)
            return utils.resolve_singleton(processed_example)

        if Context.root_block:
            self.dataset.click(
                load_example,
                inputs=[self.dataset],
                outputs=self.inputs_with_examples + (self.outputs if self.cache_examples else []),
                postprocess=False,
                queue=False,
            )

        await self.cache()

    async def cache(self) -> None:
        if Context.root_block is None:
            raise ValueError("Cannot cache examples if not in a Blocks context")

        cache_logger = CSVLogger()

        # create a fake dependency to process the examples and get the predictions
        dependency = Context.root_block.set_event_trigger(
            event_name="fake_event",
            fn=self.fn,
            inputs=self.inputs_with_examples,
            outputs=self.outputs,
            preprocess=self.preprocess and not self._api_mode,
            postprocess=self.postprocess and not self._api_mode,
            batch=self.batch,
        )

        fn_index = Context.root_block.dependencies.index(dependency)
        cache_logger.setup(self.outputs, self.cached_folder)
        for example_id, _ in enumerate(self.examples):
            processed_input = self.processed_examples[example_id]
            prediction = await Context.root_block.process_api(
                fn_index=fn_index, inputs=processed_input, request=None
            )
            output = prediction["data"]
            cache_logger.flag(output)
        # Remove the "fake_event" to prevent bugs in loading interfaces from spaces
        Context.root_block.dependencies.remove(dependency)
        Context.root_block.fns.pop(fn_index)