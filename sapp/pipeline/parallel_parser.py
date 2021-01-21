# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from multiprocessing import Pool
from typing import Any, Dict, Iterable, List, Tuple, Type

from ..analysis_output import AnalysisOutput, Metadata
from .base_parser import BaseParser


log: logging.Logger = logging.getLogger("sapp")
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s")


# We are going to call this per process, so we need to pass in and return
# serializable data. And as a single arg, as far as I can tell. Which is why the
# args type looks so silly.
def parse(
    args: Tuple[Tuple[Type[BaseParser], List[str], Metadata], str]
) -> List[Dict[str, Any]]:
    (base_parser, repo_dirs, metadata), path = args

    parser = base_parser(repo_dirs)
    parser.initialize(metadata)

    with open(path) as handle:
        return list(parser.parse_handle(handle))


class ParallelParser(BaseParser):
    def __init__(self, parser_class: Type[BaseParser], repo_dirs: List[str]) -> None:
        super().__init__(repo_dirs)
        self.parser: Type[BaseParser] = parser_class

    def parse(self, input: AnalysisOutput) -> Iterable[Dict[str, Any]]:
        log.info("Parsing in parallel")
        files = list(input.file_names())

        # Pair up the arguments with each file.
        args = zip([(self.parser, self.repo_dirs, input.metadata)] * len(files), files)

        with Pool(processes=None) as pool:
            for f in pool.imap_unordered(parse, args):
                yield from f
