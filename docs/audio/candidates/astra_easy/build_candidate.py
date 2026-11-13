#!/usr/bin/env python3
"""Build and validate an isolated easy candidate using the measured beat grid."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ANALYSIS = ROOT / 'docs/audio/hladini_shakti_excerpt.analysis.json'
PACKAGE = HERE / 'kiirtaniyas.hladini_excerpt_astra_easy.cytoidlevel'


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')


def main():
    analysis = json.loads(ANALYSIS.read_text())
    beats = analysis['beats']
    first = beats[0]['time_seconds']
    # Keep exact measured intervals, including all unused beats. No BPM clamp.
    tempos = [{'tick': i * 480, 'value': round((b['time_seconds'] - a['time_seconds']) * 1e6)}
              for i, (a, b) in enumerate(zip(beats, beats[1:]))]
    tempos.append({'tick': (len(beats) - 1) * 480, 'value': tempos[-1]['value']})
    selected = []
    for i, beat in enumerate(beats):
        t = beat['time_seconds']
        if t < 2 or t > 207:
            continue
        # Stable half-time pulse. One measured-onset quarter pulse per 16 beats
        # in the middle provides an occasional three-note phrase, then releases.
        if i % 2 == 0 or (70 <= t < 190 and i % 16 == 9 and beat['matched_to_onset']):
            selected.append(i)
    pages = [{'start_tick': i * 1920, 'end_tick': (i + 1) * 1920,
              'scan_line_direction': 1 if i % 2 == 0 else -1}
             for i in range((len(beats) + 3) // 4)]
    xs = [0.34, 0.46, 0.62, 0.50, 0.36, 0.48, 0.64, 0.52]
    notes = [{'page_index': i // 4, 'type': 0, 'id': n, 'tick': i * 480,
              'x': xs[n % len(xs)], 'has_sibling': False, 'hold_tick': 0,
              'next_id': 0, 'is_forward': False, 'approach_rate': 1.0}
             for n, i in enumerate(selected)]
    chart = {'format_version': 0, 'time_base': 480, 'music_offset': -first,
             'display_background': False, 'page_list': pages, 'tempo_list': tempos,
             'event_order_list': [], 'note_list': notes}
    level = {'schema_version': 2, 'version': 1,
             'id': 'kiirtaniyas.hladini_excerpt_astra_easy',
             'title': 'Hladini Shakti Kiirtana - Excerpt (Astra Easy Candidate)',
             'artist': 'Bhuvanesh', 'charter': 'Astra - measured timing candidate',
             'music': {'path': 'music.mp3'}, 'music_preview': {'path': 'music.mp3'},
             'charts': [{'type': 'easy', 'difficulty': 3, 'path': 'chart.easy.json'}]}
    save('chart.easy.json', chart)
    save('level.json', level)
    subprocess.run(['python3', str(ROOT / 'tools/audio/package_kiirtan_level.py'),
                    '--source', analysis['source']['path'], '--start', '180',
                    '--duration', '210', '--level-dir', str(HERE), '--output', str(PACKAGE)], check=True)
    spec = importlib.util.spec_from_file_location('validator', ROOT / 'tools/audio/validate_c2_level.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    base = validator.validate(HERE / 'level.json', None)
    times = [validator.chart_time(n['tick'], tempos, 480) - chart['music_offset'] for n in notes]
    errors = [abs(t - beats[i]['time_seconds']) for t, i in zip(times, selected)]
    grid_errors = [abs(validator.chart_time(i * 480, tempos, 480) + first - b['time_seconds'])
                   for i, b in enumerate(beats)]
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert max(grid_errors) < 0.00001
    assert min(gaps) >= 0.45
    assert all(pages[n['page_index']]['start_tick'] <= n['tick'] < pages[n['page_index']]['end_tick'] for n in notes)
    assert all(n['id'] == i and n['type'] == 0 for i, n in enumerate(notes))
    assert all(a['end_tick'] == b['start_tick'] for a, b in zip(pages, pages[1:]))
    with zipfile.ZipFile(PACKAGE) as package:
        assert package.testzip() is None
        assert set(package.namelist()) == {'level.json', 'chart.easy.json', 'music.mp3'}
        for name in ['level.json', 'chart.easy.json']:
            assert package.read(name) == (HERE / name).read_bytes()
        audio = package.read('music.mp3')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration:stream=sample_rate,channels', '-of', 'json', 'pipe:0'],
                           input=audio, capture_output=True, check=True)
    audio_info = json.loads(probe.stdout)
    # Pipe MP3 duration may be absent. Decode and count PCM frames instead.
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'pipe:0', '-f', 's16le',
                          '-acodec', 'pcm_s16le', 'pipe:1'], input=audio, capture_output=True, check=True).stdout
    duration = len(pcm) / (48000 * 2 * 2)
    assert 209.95 <= duration <= 210.05
    report = {'status': 'ok', 'base_c2_validator': base,
              'selected_beat_indices': selected,
              'analysis_sha256': hashlib.sha256(ANALYSIS.read_bytes()).hexdigest(),
              'all_358_grid_points_max_error_seconds': max(grid_errors),
              'selected_notes_max_error_seconds': max(errors),
              'first_note_audio_seconds': times[0], 'last_note_audio_seconds': times[-1],
              'notes_per_second_full_excerpt': len(notes) / 210,
              'minimum_inter_note_seconds': min(gaps), 'maximum_inter_note_seconds': max(gaps),
              'maximum_horizontal_step': max(abs(a['x'] - b['x']) for a, b in zip(notes, notes[1:])),
              'onset_matched_notes': sum(beats[i]['matched_to_onset'] for i in selected),
              'predicted_pulse_notes': sum(not beats[i]['matched_to_onset'] for i in selected),
              'package_members': ['level.json', 'chart.easy.json', 'music.mp3'],
              'package_crc_and_json_identity': 'pass', 'audio_decoded_seconds': duration,
              'audio_probe': audio_info,
              'page_membership_continuity_ids_clicks_only': 'pass',
              'human_listening_and_device_playtest': 'pending'}
    save('validation.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'selected_beat_indices'}, indent=2))


if __name__ == '__main__':
    main()
