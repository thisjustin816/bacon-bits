"""Bound UI navigation so a missed input reports a failure rather than hanging."""
def select_row(get, press, target):
 for _ in range(4):
  if get('audio_row')==target:return
  press('down')
 assert get('audio_row')==target,('Audio row unreachable',target,get('audio_row'))

def lower_index(get, press, target=0):
 for _ in range(60):
  current=get('tone_index')
  if current<=target:return
  press('left')
  assert get('tone_index')<current,('Audio frequency input stalled',current)
 raise AssertionError(('Audio frequency target unreachable',target,get('tone_index')))
