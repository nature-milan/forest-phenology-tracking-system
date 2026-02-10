from pathlib import Path

from fpts.ingestion.mod13q1 import sha256_file


def test_sha256_file_is_deterministic(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"abc")
    assert sha256_file(p) == sha256_file(p)
