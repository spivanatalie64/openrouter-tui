Issue: Massive Test Suite Signature Mismatch

Description:
A massive test suite (30,000 tests) failed because it expected `_parse_stream_line` to return a `str`, but the function signature had been updated to return `tuple[str, Optional[Usage]]`.

Fix:
Updated `tests/test_massive.py` to correctly unpack the tuple and assert against the expected values.

Resolution:
Fixed and verified. All 30,000+ tests now pass.

Author: Natalie Spiva <natalie@acreetionos.org>
