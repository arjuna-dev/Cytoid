#!/usr/bin/env python3
"""Build and validate an isolated measured-grid medium candidate."""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
ANALYSIS = ROOT / 'docs/audio/hladini_shakti_excerpt.analysis.json'
AUDIO = ROOT / 'engines/unity/Assets/Kiirtaniyas/Audio/Hladini_shakti_excerpt.mp3'
spec = importlib.util.spec_from_file_location('c2_validator', ROOT / 'tools/audio/validate_c2_level.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')


def main():
    analysis = json.loads(ANALYSIS.read_text())
    beats = [b['time_seconds'] for b in analysis['beats']]
    count = len(beats)
    tempos = [{'tick': i * 480, 'value': round((b - a) * 1000000)}
              for i, (a, b) in enumerate(zip(beats, beats[1:]))]
    tempos.append({'tick': (count - 1) * 480, 'value': tempos[-1]['value']})
    pages = [{'start_tick': i * 1920, 'end_tick': (i + 1) * 1920,
              'scan_line_direction': 1 if i % 2 == 0 else -1}
             for i in range((count + 3) // 4)]
    scheduled = []
    chains = list(range(24, count - 8, 32))
    holds = list(range(10, count - 4, 16))
    chords = list(range(20, count - 8, 16))
    reserved = {i + 1 for i in chains}
    offbeats = []

    def add(tick, x, kind=0, duration=0, chain=None):
        scheduled.append({'tick': tick, 'x': x, 'type': kind,
                          'hold_tick': duration, '_chain': chain})

    for i in range(count):
        if i in reserved:
            continue
        # Alternating hands repeat a short, stable phrase. All patterns use
        # the same two broad lanes; chains make a small outward arc.
        x = (0.30, 0.70, 0.38, 0.62)[i % 4]
        if i in chains:
            for slot, px in enumerate((0.30, 0.38, 0.46)):
                add(i * 480 + slot * 240, px, 3 if slot == 0 else 4, chain=i)
        elif i in holds:
            add(i * 480, x, 1, 480)
        else:
            add(i * 480, x)
            if i in chords:
                add(i * 480, 0.70 if x < 0.5 else 0.30)
        # Sparse opening and ending, alternating eighths in the body.
        # Every fourth 16-beat phrase breathes with only one eighth per bar.
        sparse = i < 16 or i >= count - 16 or (i // 16) % 4 == 3
        if (i % 4 == 1 or (not sparse and i % 4 == 3)) and i < count - 1:
            if i not in holds and i not in chains:
                add(i * 480 + 240, 0.36 if x > 0.5 else 0.64)
                offbeats.append(i)
    scheduled.sort(key=lambda n: (n['tick'], n['x']))
    links = defaultdict(list)
    counts = Counter(n['tick'] for n in scheduled)
    for idx, n in enumerate(scheduled):
        chain = n.pop('_chain')
        n.update(id=idx, page_index=n['tick'] // 1920, next_id=0,
                 has_sibling=counts[n['tick']] > 1, is_forward=False, approach_rate=1.0)
        if chain is not None:
            links[chain].append(idx)
    for ids in links.values():
        for a, b in zip(ids, ids[1:]):
            scheduled[a]['next_id'] = b
    chart = dict(format_version=0, time_base=480, music_offset=-beats[0],
                 display_background=False, page_list=pages, tempo_list=tempos,
                 event_order_list=[], note_list=scheduled)
    level = dict(schema_version=2, version=1, id='kiirtaniyas.hladini_excerpt_astra_medium',
                 title='Hladini Shakti Kiirtana - Excerpt (Astra Medium Candidate)',
                 artist='Bhuvanesh', charter='Kiirtaniyas United - Astra candidate',
                 music={'path': 'music.mp3'}, music_preview={'path': 'music.mp3'},
                 charts=[dict(type='hard', name='Medium (Astra candidate)', difficulty=6,
                              path='chart.medium.json')])
    write('chart.medium.json', chart)
    write('level.json', level)
    # The existing validator requires an easy entry. A temporary metadata
    # adapter points at exactly the same chart, without changing package type.
    adapter = {**level, 'charts': [{**level['charts'][0], 'type': 'easy'}]}
    write('validator_adapter.json', adapter)
    baseline = validator.validate(OUT / 'validator_adapter.json', None)
    write('c2_validator_output.json', {'status': 'ok', **baseline,
                                      'adapter_reason': 'Validator is easy-only; packaged chart type is hard.'})
    times = [validator.chart_time(n['tick'], tempos, 480) for n in scheduled]
    errors = []
    for n, t in zip(scheduled, times):
        i, frac = divmod(n['tick'], 480)
        expected = beats[i] - beats[0]
        if frac:
            expected += (beats[i + 1] - beats[i]) * frac / 480
        errors.append(abs(t - expected))
        page = pages[n['page_index']]
        assert page['start_tick'] <= n['tick'] < page['end_tick']
        assert n['tick'] + n['hold_tick'] <= page['end_tick']
        if n['hold_tick']:
            assert not any(n['tick'] < other['tick'] < n['tick'] + n['hold_tick'] for other in scheduled)
    assert max(errors) < 0.000001
    assert max(counts.values()) == 2
    for tick, multiplicity in counts.items():
        if multiplicity > 1:
            simultaneous = [n for n in scheduled if n['tick'] == tick]
            assert all(n['type'] == 0 for n in simultaneous)
            assert abs(simultaneous[0]['x'] - simultaneous[1]['x']) >= 0.3
    for ids in links.values():
        assert len(ids) == 3 and scheduled[ids[0]]['type'] == 3
        assert all(scheduled[n]['type'] == 4 for n in ids[1:])
        assert scheduled[ids[-1]]['next_id'] == 0
        for a, b in zip(ids, ids[1:]):
            assert scheduled[a]['next_id'] == b and scheduled[b]['tick'] > scheduled[a]['tick']
    distinct = sorted(set(times))
    intervals = [b - a for a, b in zip(distinct, distinct[1:])]
    package_name = level['id'] + '.cytoidlevel'
    entries = {'level.json': (OUT / 'level.json').read_bytes(),
               'chart.medium.json': (OUT / 'chart.medium.json').read_bytes(),
               'music.mp3': AUDIO.read_bytes()}
    with zipfile.ZipFile(OUT / package_name, 'w') as package:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            package.writestr(info, data)
    with zipfile.ZipFile(OUT / package_name) as package:
        assert package.testzip() is None
        assert all(package.read(name) == data for name, data in entries.items())
    report = dict(status='ok', candidate='Astra medium-thinking medium',
                  level='level.json', chart='chart.medium.json', package=package_name,
                  engine_difficulty_id='hard', conceptual_difficulty='medium',
                  measured_beat_count=count, note_count=len(scheduled),
                  note_density_per_second=round(len(scheduled) / 210, 4),
                  note_density_per_measured_beat=round(len(scheduled) / count, 4),
                  type_counts=dict(sorted(Counter(str(n['type']) for n in scheduled).items())),
                  hold_count=len(holds), drag_chain_count=len(chains),
                  chord_slot_count=sum(v > 1 for v in counts.values()),
                  max_simultaneous_notes=max(counts.values()),
                  max_notes_per_page=max(Counter(n['page_index'] for n in scheduled).values()),
                  page_count=len(pages), beats_per_page=4, tempo_count=len(tempos),
                  offbeat_count=len(offbeats) + len(chains),
                  min_distinct_note_interval_seconds=round(min(intervals), 6),
                  mean_distinct_note_interval_seconds=round(sum(intervals) / len(intervals), 6),
                  chart_duration_seconds=round(times[-1], 6),
                  max_measured_grid_error_seconds=round(max(errors), 9),
                  mean_measured_grid_error_seconds=round(sum(errors) / len(errors), 9),
                  structure=dict(chain_starts=chains, hold_starts=holds, chord_beats=chords),
                  package_sha256=hashlib.sha256((OUT / package_name).read_bytes()).hexdigest(),
                  audio_sha256=hashlib.sha256(entries['music.mp3']).hexdigest(),
                  playtest_status='Not playtested; deterministic checks only')
    write('validation.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
