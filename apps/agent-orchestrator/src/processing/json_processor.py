#!/usr/bin/env python3
"""
High-performance JSON Processing with Multiprocessing
Optimized for large JSON payloads and batch processing
"""

import asyncio
import json

try:
    import orjson  # Faster JSON library

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .multiprocess_executor import get_process_pool

logger = logging.getLogger(__name__)


class FastJSONProcessor:
    """High-performance JSON processor using multiprocessing and orjson"""

    def __init__(self, use_multiprocessing: bool = True):
        self.use_multiprocessing = use_multiprocessing
        self.pool = None

    async def __aenter__(self):
        if self.use_multiprocessing:
            self.pool = await get_process_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Pool is managed globally, don't shutdown here
        pass

    async def parse_json(self, data: Union[str, bytes]) -> Dict:
        """Parse single JSON string/bytes with optimal performance"""
        if HAS_ORJSON:
            if isinstance(data, str):
                data = data.encode("utf-8")

            try:
                # Use orjson for fast parsing
                return orjson.loads(data)
            except Exception as e:
                # Fallback to standard json
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                return json.loads(data)
        else:
            # Use standard json
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data)

    async def parse_json_batch(
        self, json_strings: List[Union[str, bytes]]
    ) -> List[Dict]:
        """Parse multiple JSON strings using multiprocessing for large batches"""
        if not json_strings:
            return []

        # For small batches, use single process
        if len(json_strings) < 10 or not self.use_multiprocessing:
            results = []
            for json_str in json_strings:
                try:
                    if HAS_ORJSON:
                        if isinstance(json_str, str):
                            json_str = json_str.encode("utf-8")
                        results.append(orjson.loads(json_str))
                    else:
                        if isinstance(json_str, bytes):
                            json_str = json_str.decode("utf-8")
                        results.append(json.loads(json_str))
                except Exception as e:
                    results.append({"error": str(e)})
            return results

        # For large batches, use multiprocessing
        if self.pool:
            return await self.pool.parse_json_batch(
                [s if isinstance(s, str) else s.decode("utf-8") for s in json_strings]
            )

        # Fallback
        return await asyncio.gather(*[self.parse_json(s) for s in json_strings])

    async def serialize_json(
        self, obj: Any, pretty: bool = False, sort_keys: bool = False
    ) -> bytes:
        """Serialize object to JSON bytes with optimal performance"""
        if HAS_ORJSON:
            try:
                # Use orjson for fast serialization
                option = 0
                if pretty:
                    option |= orjson.OPT_INDENT_2
                if sort_keys:
                    option |= orjson.OPT_SORT_KEYS

                return orjson.dumps(obj, option=option)
            except Exception:
                # Fallback to standard json
                return json.dumps(
                    obj, indent=2 if pretty else None, sort_keys=sort_keys
                ).encode("utf-8")
        else:
            # Use standard json
            return json.dumps(
                obj, indent=2 if pretty else None, sort_keys=sort_keys
            ).encode("utf-8")

    async def load_json_file(self, file_path: Union[str, Path]) -> Dict:
        """Load JSON from file with optimal performance"""
        path = Path(file_path)

        # Read file asynchronously
        loop = asyncio.get_event_loop()

        def _read_file():
            with open(path, "rb") as f:
                return f.read()

        data = await loop.run_in_executor(None, _read_file)

        # Parse JSON
        return await self.parse_json(data)

    async def save_json_file(
        self,
        obj: Any,
        file_path: Union[str, Path],
        pretty: bool = True,
        atomic: bool = True,
    ):
        """Save JSON to file with optimal performance and atomic writes"""
        path = Path(file_path)

        # Serialize JSON
        data = await self.serialize_json(obj, pretty=pretty)

        # Write file asynchronously
        loop = asyncio.get_event_loop()

        def _write_file():
            if atomic:
                # Atomic write using temp file
                temp_path = path.with_suffix(".tmp")
                with open(temp_path, "wb") as f:
                    f.write(data)
                temp_path.replace(path)
            else:
                with open(path, "wb") as f:
                    f.write(data)

        await loop.run_in_executor(None, _write_file)

    async def stream_parse_jsonl(
        self, file_path: Union[str, Path], batch_size: int = 1000
    ):
        """Stream parse JSONL file with batched processing"""
        path = Path(file_path)

        async def read_lines():
            loop = asyncio.get_event_loop()

            def _read():
                with open(path, "r") as f:
                    batch = []
                    for line in f:
                        batch.append(line.strip())
                        if len(batch) >= batch_size:
                            yield batch
                            batch = []
                    if batch:
                        yield batch

            for batch in _read():
                parsed = await self.parse_json_batch(batch)
                for item in parsed:
                    yield item

        async for item in read_lines():
            yield item

    async def validate_json_schema(
        self, data: Dict, schema: Dict
    ) -> Tuple[bool, Optional[List[str]]]:
        """Validate JSON against schema (requires jsonschema package)"""
        try:
            import jsonschema

            # Run validation in process pool for large schemas
            if self.use_multiprocessing and self.pool:

                def _validate():
                    try:
                        jsonschema.validate(data, schema)
                        return True, None
                    except jsonschema.ValidationError as e:
                        return False, [str(e)]

                return await self.pool.run_cpu_intensive(_validate)
            else:
                # Direct validation for small schemas
                try:
                    jsonschema.validate(data, schema)
                    return True, None
                except jsonschema.ValidationError as e:
                    return False, [str(e)]

        except ImportError:
            logger.warning("jsonschema package not installed, skipping validation")
            return True, None


# Global instance for convenience
_global_processor: Optional[FastJSONProcessor] = None


async def get_json_processor() -> FastJSONProcessor:
    """Get or create global JSON processor"""
    global _global_processor
    if _global_processor is None:
        _global_processor = FastJSONProcessor()
    return _global_processor
