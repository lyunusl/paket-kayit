# Paket Kayıt - Developed by AugeLab
# Copyright (c) 2026 AugeLab. Licensed under the MIT License (see LICENSE).

from studio.custom_block import (
    Block, CheckBox, DropDown, Label, SocketTypes, TextInput, add_block,
)

import cv2
import time
import os
import sys
import json

class PaketKamera(Block):
    op_code = 'PaketKamera'
    input_sockets = [
        
    ]
    output_sockets = [
        SocketTypes.ImageAny('Frame', multiple=False),
        SocketTypes.String('Camera Status', multiple=False)
    ]
    _augelab_generated_spec_version = 1
    _augelab_output_names = ('Frame', 'Camera Status')

    def init(self):
        self.op_title = 'Paket Kamera'
        self.width = 280
        self.height = 240
        self.tooltip = "Opens the USB camera with the given index (0 = first camera) at the selected resolution, with no manual scan; retries every 2 s. Values saved on the Paket Kayıt settings page override this block's settings."
        self.param['label:camera_index'] = Label(text='Kamera numarası (0, 1, 2...)')
        self.param['camera_index'] = TextInput(name='camera_index', text='0')
        self.param['label:resolution'] = Label(text='Çözünürlük')
        self.param['resolution'] = DropDown(name='resolution', items=['640 x 480', '1280 x 720', '1920 x 1080'], selected_index=1, serializable=True)
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
        defaults['camera_index'] = int(parameters['camera_index'] or 0)
        defaults['resolution'] = str(parameters['resolution'] or '1280 x 720')

        now = time.time()
        idx = int(S.get('camera_index', defaults['camera_index']))
        res = str(S.get('resolution', defaults['resolution']))
        w, h = [int(v) for v in res.split('x')]
        key = (idx, res)
        cap = state.get('cap')
        if state.get('key') != key:
            if cap is not None:
                cap.release()
            cap = None
            state['cap'] = None
            state['key'] = key
            state['retry'] = 0
        if cap is None and now >= state.get('retry', 0):
            backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            c = cv2.VideoCapture(idx, backend)
            if c.isOpened():
                c.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                c.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                cap = c
                state['cap'] = c
            else:
                c.release()
                state['retry'] = now + 2
        frame = None
        if cap is not None:
            ok, fr = cap.read()
            if ok and fr is not None:
                frame = fr
                status = 'Kamera ' + str(idx) + ' · ' + str(fr.shape[1]) + 'x' + str(fr.shape[0])
            else:
                cap.release()
                state['cap'] = None
                state['retry'] = now + 2
                status = 'Kamera ' + str(idx) + ' okunamadı, yeniden deneniyor'
        else:
            status = 'Kamera ' + str(idx) + ' bulunamadı, yeniden deneniyor'
        outputs['Frame'] = frame
        outputs['Camera Status'] = status

    def run(self):
        inputs = {
            
        }
        parameters = {
            'camera_index': int(self.param['camera_index'].value),
            'resolution': self.param['resolution'].selected_item
        }
        state = self._augelab_generated_state
        outputs = {
            'Frame': None,
            'Camera Status': None
        }
        self._process(inputs, parameters, state, outputs)
        unknown = set(outputs).difference(self._augelab_output_names)
        if unknown:
            raise ValueError(f"Undeclared generated outputs: {sorted(unknown)}")
        for output_name in self._augelab_output_names:
            self.output[output_name].data = outputs[output_name]


add_block(PaketKamera.op_code, PaketKamera)
