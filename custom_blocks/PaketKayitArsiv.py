# Paket Kayıt - Developed by AugeLab
# Copyright (c) 2026 AugeLab. Licensed under the MIT License (see LICENSE).

from studio.custom_block import (
    Block, CheckBox, DropDown, Label, SocketTypes, TextInput, add_block,
)

import time
import re
import os
import cv2
import sys
import json

class PaketKayitArsiv(Block):
    op_code = 'PaketKayitArsiv'
    input_sockets = [
        SocketTypes.String('Query', multiple=False),
        SocketTypes.String('Folder', multiple=False)
    ]
    output_sockets = [
        SocketTypes.ImageAny('Frame', multiple=False),
        SocketTypes.String('Found File', multiple=False),
        SocketTypes.String('Results', multiple=False),
        SocketTypes.Integer('Count', multiple=False)
    ]
    _augelab_generated_spec_version = 1
    _augelab_output_names = ('Frame', 'Found File', 'Results', 'Count')

    def init(self):
        self.op_title = 'Paket Kayıt Arşivi'
        self.width = 280
        self.height = 210
        self.tooltip = "Searches the Folder for <barcode>_<YYYYMMDD_HHMMSS>.mp4 recordings matching the Query, plays the newest and lists up to 10. Once an hour it deletes only files with that naming pattern older than the retention days (0 = never). Settings page values override this block's settings."
        self.param['label:keep_days'] = Label(text='Saklama süresi (gün, 0 = silme)')
        self.param['keep_days'] = TextInput(name='keep_days', text='90')
        self.param['loop'] = CheckBox(name='loop', text='Kaydı döngüde oynat', init_state=True)
        self._augelab_generated_state = {}

    @staticmethod
    def _process(inputs, parameters, state, outputs):
        cfg = sys.__dict__.setdefault('_paket_kayit_cfg', {})
        defaults = cfg.setdefault('defaults', {})
        if 'data' not in cfg:
            path = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'PaketKayit', 'ayarlar.json')
            try:
                with open(path, encoding='utf-8') as fh:
                    data = dict(json.load(fh))
            except Exception:
                data = {}
            cfg['path'] = path
            cfg['data'] = data
        S = cfg['data']
        defaults['keep_days'] = int(parameters['keep_days'] or 0)
        keep = int(S.get('keep_days', defaults['keep_days']) or 0)

        now = time.time()
        outputs['Frame'] = None
        outputs['Found File'] = ''
        outputs['Results'] = ''
        outputs['Count'] = 0
        folder = str(inputs['Folder'] or '').strip()
        q = str(inputs['Query'] or '').strip()
        pat = re.compile(r'^(.+)_(\d{8})_(\d{6})\.mp4$')
        if not folder or not os.path.isdir(folder):
            outputs['Results'] = 'Kayıt klasörü bulunamadı'
            return

        # retention: at most once per hour, only files written by Paket Kayıt
        if keep > 0 and now - state.get('last_clean', 0) > 3600:
            state['last_clean'] = now
            limit = now - keep * 86400
            for f in os.listdir(folder):
                if pat.match(f):
                    p = os.path.join(folder, f)
                    try:
                        if os.path.getmtime(p) < limit:
                            os.remove(p)
                    except Exception:
                        pass

        safe_q = re.sub(r'[^A-Za-z0-9_-]', '_', q)
        changed = q != state.get('q')
        if changed or now - state.get('listed', 0) > 5:
            state['listed'] = now
            files = []
            if safe_q:
                for f in os.listdir(folder):
                    m = pat.match(f)
                    if m and safe_q in m.group(1):
                        files.append((m.group(2) + m.group(3), f))
            files.sort(reverse=True)
            state['files'] = [f for _, f in files]
        if changed:
            state['q'] = q
            cap = state.get('cap')
            if cap is not None:
                cap.release()
            state['cap'] = None
            state['path'] = ''
            state['frame'] = None
            if state['files']:
                path = os.path.join(folder, state['files'][0])
                cap = cv2.VideoCapture(path)
                state['cap'] = cap
                state['path'] = path
                state['t0'] = now
                state['idx'] = -1
                state['fps'] = cap.get(cv2.CAP_PROP_FPS) or 25.0
                state['n'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        cap = state.get('cap')
        if cap is not None:
            fps = state['fps'] if state['fps'] > 0 else 25.0
            target = int((now - state['t0']) * fps)
            n = state['n']
            if n > 0 and target >= n:
                if parameters['loop']:
                    state['t0'] = now
                    target = 0
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    state['idx'] = -1
                else:
                    target = n - 1
            if target - state['idx'] > 30:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target)
                state['idx'] = target - 1
            steps = 0
            while state['idx'] < target and steps < 30:
                ok, fr = cap.read()
                if not ok:
                    break
                state['idx'] += 1
                state['frame'] = fr
                steps += 1
            outputs['Frame'] = state['frame']
            outputs['Found File'] = state['path']

        lines = []
        for f in state.get('files', [])[:10]:
            m = pat.match(f)
            d, t = m.group(2), m.group(3)
            lines.append(d[6:8] + '.' + d[4:6] + '.' + d[0:4] + ' ' + t[0:2] + ':' + t[2:4] + ':' + t[4:6] + '  ·  ' + m.group(1))
        if lines:
            outputs['Results'] = '\n'.join(lines)
        else:
            outputs['Results'] = 'Kayıt bulunamadı' if q else 'Aramak için barkod yazın'
        outputs['Count'] = len(state.get('files', []))

    def run(self):
        inputs = {
            'Query': self.input['Query'].data,
            'Folder': self.input['Folder'].data
        }
        parameters = {
            'keep_days': int(self.param['keep_days'].value),
            'loop': bool(self.param['loop'].is_checked)
        }
        state = self._augelab_generated_state
        outputs = {
            'Frame': None,
            'Found File': None,
            'Results': None,
            'Count': None
        }
        self._process(inputs, parameters, state, outputs)
        unknown = set(outputs).difference(self._augelab_output_names)
        if unknown:
            raise ValueError(f"Undeclared generated outputs: {sorted(unknown)}")
        for output_name in self._augelab_output_names:
            self.output[output_name].data = outputs[output_name]


add_block(PaketKayitArsiv.op_code, PaketKayitArsiv)
