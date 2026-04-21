Issue: Stream Parsing Regression (TypeError on Bytes)

Description:
During testing, a `TypeError` was encountered in `openrouter_client.py` within `_parse_stream_line`. When the input was a `bytes` object that failed to decode as UTF-8, the function would attempt to call `.startswith()` on the original `bytes` object using a string argument (`"data:"`), which is invalid in Python 3.

Fix:
Updated `_parse_stream_line` to assign an empty string on decoding failure, ensuring that subsequent string operations are safe.

Resolution:
Fixed and verified with `tests/test_openrouter_client.py::test_parse_stream_line_bytes_error`.

Author: Natalie Spiva <natalie@acreetionos.org>
