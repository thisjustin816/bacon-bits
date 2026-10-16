"""Publish complete generated files, preserving unchanged content."""
import os
from pathlib import Path

def write_generated(path,content):
 path=Path(path)
 if path.exists() and path.read_text()==content:return
 temporary=path.with_name(path.name+f'.{os.getpid()}.tmp')
 try:
  temporary.write_text(content);os.replace(temporary,path)
 finally:
  if temporary.exists():temporary.unlink()
