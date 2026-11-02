# Paket Kayıt - Developed by AugeLab
# Copyright (c) 2026 AugeLab. Licensed under the MIT License (see LICENSE).

from studio.custom_block import (
    Block, CheckBox, DropDown, Label, SocketTypes, TextInput, add_block,
)

import sys
import threading
import time
import os
import json
import cv2
import numpy
import collections
import importlib

class PaketWebGiris(Block):
    op_code = 'PaketWebGiris'
    input_sockets = [
        SocketTypes.ImageAny('Frame', multiple=False),
        SocketTypes.String('Default Folder', multiple=False)
    ]
    output_sockets = [
        SocketTypes.String('Barcode', multiple=False),
        SocketTypes.Boolean('Scan', multiple=False),
        SocketTypes.ImageAny('Frame', multiple=False),
        SocketTypes.String('Folder', multiple=False)
    ]
    _augelab_generated_spec_version = 1
    _augelab_output_names = ('Barcode', 'Scan', 'Frame', 'Folder')

    def init(self):
        self.op_title = 'Paket Barkod Girişi'
        self.width = 280
        self.height = 270
        self.tooltip = "Reads barcodes from the camera frame with zbar (pyzbar, the engine behind AugeLab's Barcode Reader) or OpenCV when zbar is missing, and merges them with codes scanned into the Paket Kayıt web page; Scan is TRUE for one tick per code. Repeated reads are required to filter phantom codes. Draws a green box around codes, shows a 'camera not found' frame without a camera, and outputs the recording folder."
        self.param['label:port'] = Label(text='Arayüz portu')
        self.param['port'] = TextInput(name='port', text='8080')
        self.param['label:cooldown'] = Label(text='Aynı barkodu yeniden sayma süresi (sn)')
        self.param['cooldown'] = TextInput(name='cooldown', text='5')
        self.param['draw_box'] = CheckBox(name='draw_box', text='Barkodu kare içine al', init_state=True)
        self._augelab_generated_state = {}

    @staticmethod
    def _process(inputs, parameters, state, outputs):
        BOX_HOLD = 0.6  # keep a found box on screen briefly so it does not flicker
        CONFIRM_WINDOW = 1.5
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
        defaults['cooldown'] = float(parameters['cooldown'] or 0) or 5.0
        defaults['draw_box'] = bool(parameters['draw_box'])
        defaults['folder'] = str(inputs['Default Folder'] or '').strip()
        cooldown = float(S.get('cooldown', defaults['cooldown']) or 0) or 5.0
        draw_box = bool(S.get('draw_box', defaults['draw_box']))
        folder = str(S.get('folder') or defaults['folder']).strip()

        now = time.time()
        g = sys.__dict__.setdefault('_paket_kayit_web', {})
        port = int(parameters['port'] or 8080)
        web = g.setdefault(port, {'jpeg': None, 'state': {}, 'scans': [], 'folder': '', 'lock': threading.Lock()})
        hits = state.setdefault('hits', {})

        # zbar (pyzbar) reads 1D codes far better than OpenCV; the setup installs it, OpenCV is the fallback
        if 'zbar' not in state:
            try:
                state['zbar'] = importlib.import_module('pyzbar.pyzbar')
            except Exception:
                state['zbar'] = None
            web['reader'] = 'zbar' if state['zbar'] else 'opencv'
        zbar = state['zbar']
        confirm_hits = 2 if zbar else 3  # texture produces one-off phantom reads, OpenCV more often than zbar

        found = []
        frame = inputs['Frame']
        if frame is not None:
            try:
                if zbar:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
                    for r in zbar.decode(gray):
                        pts = [(p.x, p.y) for p in r.polygon]
                        if len(pts) < 4:
                            x, y, w, h = r.rect
                            pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                        hull = cv2.convexHull(numpy.array(pts, numpy.int32)).reshape(-1, 2)
                        found.append((hull, r.data.decode('utf-8', 'ignore')))
                else:
                    if 'det' not in state:
                        state['det'] = cv2.barcode.BarcodeDetector()
                    ok, decoded, _types, pts = state['det'].detectAndDecodeWithType(frame)
                    if ok and pts is not None and len(pts):
                        quads = numpy.asarray(pts).reshape(-1, 4, 2).astype(numpy.int32)
                        found = list(zip(quads, list(decoded or [])))
            except Exception:
                found = []

        codes = []
        confirmed_boxes = []
        for quad, text in found:
            text = (text or '').strip()
            if len(text) < 6 or collections.Counter(text).most_common(1)[0][1] > 0.6 * len(text):
                continue
            recent = [t for t in hits.get(text, []) if now - t < CONFIRM_WINDOW] + [now]
            hits[text] = recent
            if len(recent) >= confirm_hits:
                codes.append(text)
                confirmed_boxes.append((quad, text))
        for k in [k for k, v in hits.items() if now - v[-1] > CONFIRM_WINDOW]:
            del hits[k]
        if confirmed_boxes:
            state['boxes'] = confirmed_boxes
            state['box_t'] = now

        # a code in view keeps refreshing its time, so it counts once until it leaves for longer than the cooldown
        seen = web.setdefault('cam_seen', {})
        for c in codes:
            if now - seen.get(c, 0) > cooldown:
                with web['lock']:
                    web['scans'].append(c)
            seen[c] = now
        for c in [k for k, t in seen.items() if now - t > 60]:
            del seen[c]

        code = ''
        with web['lock']:
            if web['scans']:
                code = web['scans'].pop(0)
                web['beep'] = web.get('beep', 0) + 1
                web['last_code'] = code

        out = frame
        if frame is not None and draw_box and now - state.get('box_t', 0) < BOX_HOLD:
            out = frame.copy()
            for quad, label in state['boxes']:
                cv2.polylines(out, [quad], True, (90, 230, 70), 4, cv2.LINE_AA)
                x, y = int(quad[:, 0].min()), int(quad[:, 1].min())
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                y0 = max(th + 12, y - 8)
                cv2.rectangle(out, (x, y0 - th - 10), (x + tw + 12, y0 + 4), (90, 230, 70), -1)
                cv2.putText(out, label, (x + 6, y0 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (10, 30, 10), 2, cv2.LINE_AA)

        # without a camera the drawing and video blocks downstream fail on None; show a readable placeholder instead
        if out is None:
            res = str(S.get('resolution', defaults.get('resolution', '1280 x 720')))
            if state.get('placeholder_res') != res:
                w, h = [int(v) for v in res.split('x')]
                ph = numpy.zeros((h, w, 3), numpy.uint8)
                ph[:] = (16, 13, 11)
                for i, (line, scale) in enumerate([('Kamera bulunamadi', 1.4 * w / 1280), ('Ayarlar sekmesinden kamera numarasini kontrol edin', 0.7 * w / 1280)]):
                    (tw, th), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
                    cv2.putText(ph, line, ((w - tw) // 2, h // 2 + int(i * 60 * w / 1280)), cv2.FONT_HERSHEY_SIMPLEX, scale, (210, 210, 210), 2, cv2.LINE_AA)
                state['placeholder'] = ph
                state['placeholder_res'] = res
            out = state['placeholder']

        outputs['Barcode'] = code
        outputs['Scan'] = bool(code)
        outputs['Frame'] = out
        outputs['Folder'] = folder

    def run(self):
        inputs = {
            'Frame': self.input['Frame'].data,
            'Default Folder': self.input['Default Folder'].data
        }
        parameters = {
            'port': int(self.param['port'].value),
            'cooldown': float(self.param['cooldown'].value),
            'draw_box': bool(self.param['draw_box'].is_checked)
        }
        state = self._augelab_generated_state
        outputs = {
            'Barcode': None,
            'Scan': None,
            'Frame': None,
            'Folder': None
        }
        self._process(inputs, parameters, state, outputs)
        unknown = set(outputs).difference(self._augelab_output_names)
        if unknown:
            raise ValueError(f"Undeclared generated outputs: {sorted(unknown)}")
        for output_name in self._augelab_output_names:
            self.output[output_name].data = outputs[output_name]


add_block(PaketWebGiris.op_code, PaketWebGiris)
