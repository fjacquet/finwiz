"""File and directory reading tools.

Self-contained replacements for ``crewai_tools.FileReadTool`` and
``crewai_tools.DirectoryReadTool`` so FinWiz can depend on ``crewai`` WITHOUT
the heavy ``crewai[tools]`` extra. That extra pulls pyarrow, lancedb, pymupdf,
docker, pytube, youtube-transcript-api and more — none of which FinWiz uses; it
only needs these two file readers (for the report / discovery / rebalancing
crews to read generated outputs and JSON schemas).

Behaviour mirrors crewai_tools exactly: each tool accepts a fixed path at
construction AND an optional runtime override, so an agent can read/list
arbitrary paths discovered at call time (e.g. files surfaced by a directory
listing), not only the path baked in at construction.
"""

from __future__ import annotations

import os
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class FileReadToolSchema(BaseModel):
    """Input for :class:`FileReadTool`."""

    file_path: str = Field(..., description="Mandatory file full path to read the file")
    start_line: int | None = Field(1, description="Line number to start reading from (1-indexed)")
    line_count: int | None = Field(None, description="Number of lines to read. If None, reads the entire file")


class FileReadTool(BaseTool):
    """Read a file's content, optionally a line range.

    The path may be fixed at construction (``FileReadTool(file_path=...)``) and/or
    supplied at runtime via the ``file_path`` argument, which overrides the
    constructor default.
    """

    name: str = "Read a file's content"
    description: str = "A tool that reads the content of a file. To use this tool, provide a 'file_path' parameter with the path to the file you want to read. Optionally, provide 'start_line' to start reading from a specific line and 'line_count' to limit the number of lines read."
    args_schema: type[BaseModel] = FileReadToolSchema
    file_path: str | None = None

    def __init__(self, file_path: str | None = None, **kwargs: Any) -> None:
        """Optionally bind a default ``file_path`` for this tool instance."""
        if file_path is not None:
            kwargs["description"] = (
                f"A tool that reads file content. The default file is {file_path}, but you can provide a different "
                "'file_path' parameter to read another file. You can also specify 'start_line' and 'line_count' to "
                "read specific parts of the file."
            )
        super().__init__(**kwargs)
        self.file_path = file_path

    def _run(self, file_path: str | None = None, start_line: int | None = 1, line_count: int | None = None) -> str:
        file_path = file_path or self.file_path
        start_line = start_line or 1
        if file_path is None:
            return "Error: No file path provided. Please provide a file path either in the constructor or as an argument."
        try:
            with open(file_path, encoding="utf-8") as file:
                if start_line == 1 and line_count is None:
                    return file.read()
                start_idx = max(start_line - 1, 0)
                selected = [line for i, line in enumerate(file) if i >= start_idx and (line_count is None or i < start_idx + line_count)]
                if not selected and start_idx > 0:
                    return f"Error: Start line {start_line} exceeds the number of lines in the file."
                return "".join(selected)
        except FileNotFoundError:
            return f"Error: File not found at path: {file_path}"
        except PermissionError:
            return f"Error: Permission denied when trying to read file: {file_path}"
        except OSError as e:
            return f"Error: Failed to read file {file_path}. {e!s}"


class FixedDirectoryReadToolSchema(BaseModel):
    """Input for :class:`DirectoryReadTool` when the directory is fixed."""


class DirectoryReadToolSchema(FixedDirectoryReadToolSchema):
    """Input for :class:`DirectoryReadTool` when the directory is provided at runtime."""

    directory: str = Field(..., description="Mandatory directory to list content")


class DirectoryReadTool(BaseTool):
    """Recursively list the files inside a directory.

    The directory may be fixed at construction and/or supplied at runtime.
    """

    name: str = "List files in directory"
    description: str = "A tool that can be used to recursively list a directory's content."
    args_schema: type[BaseModel] = DirectoryReadToolSchema
    directory: str | None = None

    def __init__(self, directory: str | None = None, **kwargs: Any) -> None:
        """Optionally bind a default ``directory`` for this tool instance."""
        super().__init__(**kwargs)
        if directory is not None:
            self.directory = directory
            self.description = f"A tool that can be used to list {directory}'s content."
            self.args_schema = FixedDirectoryReadToolSchema
            self._generate_description()

    def _run(self, **kwargs: Any) -> str:
        directory: str | None = kwargs.get("directory", self.directory)
        if directory is None:
            raise ValueError("Directory must be provided.")
        if directory[-1] == "/":
            directory = directory[:-1]
        files_list = [f"{directory}/{os.path.join(root, filename).replace(directory, '').lstrip(os.path.sep)}" for root, _dirs, files in os.walk(directory) for filename in files]
        files = "\n- ".join(files_list)
        return f"File paths: \n-{files}"
