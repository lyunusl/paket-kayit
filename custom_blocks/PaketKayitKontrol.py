# Paket Kayıt - Developed by AugeLab
# Copyright (c) 2026 AugeLab. Licensed under the MIT License (see LICENSE).

from studio.custom_block import (
    Block, CheckBox, DropDown, Label, SocketTypes, TextInput, add_block,
)

import time
import datetime
import re
import os
import sys
import json

class PaketKayitKontrol(Block):
    op_code = 'PaketKayitKontrol'
    input_sockets = [
        SocketTypes.String('Barcode', multiple=False),
        SocketTypes.Boolean('Scan', multiple=False),
        SocketTypes.String('Folder', multiple=False),
        SocketTypes.String('Search Query', multiple=False)
    ]
    output_sockets = [
        SocketTypes.Boolean('Record', multiple=False),
        SocketTypes.String('File Name', multiple=False),
        SocketTypes.String('Overlay Text', multiple=False),
        SocketTypes.String('Active Barcode', multiple=False),
        SocketTypes.Number('Remaining', multiple=False),
        SocketTypes.String('Status', multiple=False),
        SocketTypes.Integer('Products', multiple=False),
        SocketTypes.Number('Max Seconds', multiple=False),
        SocketTypes.String('Station', multiple=False)
    ]
    _augelab_generated_spec_version = 1
    _augelab_output_names = ('Record', 'File Name', 'Overlay Text', 'Active Barcode', 'Remaining', 'Status', 'Products', 'Max Seconds', 'Station')

    def init(self):
        self.op_title = 'Paket Kayıt Kontrol'
        self.width = 280
        self.height = 390
        self.tooltip = "Starts and stops Save Video from barcode events. Order barcodes (prefix rule, else min. length and not an EAN/UPC product code) start <barcode>_<YYYYMMDD_HHMMSS>; the next order closes it, waits 1 s, then starts a new one. Max seconds stops it. Settings page values override this block's settings."
        self.param['label:max_seconds'] = Label(text='Maks. kayıt süresi (sn)')
        self.param['max_seconds'] = TextInput(name='max_seconds', text='45')
        self.param['label:min_length'] = Label(text='Sipariş barkodu min. uzunluk')
        self.param['min_length'] = TextInput(name='min_length', text='8')
        self.param['label:prefixes'] = Label(text='Sipariş barkodu ön ekleri (virgülle, boş = hepsi)')
        self.param['prefixes'] = TextInput(name='prefixes', text='')
        self.param['label:station'] = Label(text='Masa adı')
        self.param['station'] = TextInput(name='station', text='Masa 1')
        self.param['ean_products'] = CheckBox(name='ean_products', text='EAN/UPC barkodları ürün say', init_state=True)
        self._augelab_generated_state = {}

    @staticmethod
    def _process(inputs, parameters, state, outputs):
        FINALIZE_GAP = 1.0  # Save Video refuses to start while the previous file is still finalizing
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
        defaults['max_seconds'] = float(parameters['max_seconds'] or 0) or 45.0
        defaults['min_length'] = int(parameters['min_length'] or 0)
        defaults['prefixes'] = str(parameters['prefixes'] or '')
        defaults['station'] = str(parameters['station'] or '')
        defaults['ean_products'] = bool(parameters['ean_products'])
        max_s = float(S.get('max_seconds', defaults['max_seconds']) or 0) or 45.0
        min_len = int(S.get('min_length', defaults['min_length']) or 0)
        prefixes = [p.strip() for p in str(S.get('prefixes', defaults['prefixes']) or '').split(',') if p.strip()]
        station = str(S.get('station', defaults['station']) or '')
        ean_on = bool(S.get('ean_products', defaults['ean_products']))

        now = time.time()
        st = state
        if 'rec' not in st:
            st.update(rec=False, name='', bc='', start=0.0, pending=None, items=[], prev_scan=False, prev_bc='', status='Barkod bekleniyor', folder_ok='', last='', gap_until=0.0)
        raw = str(inputs['Barcode'] or '')
        # a keyboard-hook reader spells out modifier keys (scanners press Shift for capitals); drop them
        bc = re.sub(r'(left |right )?(shift|caps lock|caps_lock)', '', raw).replace('space', ' ').strip()
        scan = inputs['Scan']
        folder = str(inputs['Folder'] or '').strip()
        query = str(inputs['Search Query'] or '').strip()
        if folder and st['folder_ok'] != folder:
            try:
                os.makedirs(folder, exist_ok=True)
                st['folder_ok'] = folder
            except Exception as e:
                st['status'] = 'Klasör oluşturulamadı: ' + str(e)

        # a new scan: rising edge of Scan, or a changed barcode text
        if scan is None:
            event = bool(bc) and bc != st['prev_bc']
        else:
            event = bool(bc) and ((bool(scan) and not st['prev_scan']) or (bool(scan) and bc != st['prev_bc']))
        if bc and bc != st['prev_bc']:
            st['last'] = 'son giriş: ' + bc
        st['prev_scan'] = bool(scan)
        st['prev_bc'] = bc

        looks_like_barcode = re.fullmatch(r'[A-Za-z0-9._/-]+', bc) is not None and any(ch.isdigit() for ch in bc)
        if event and not looks_like_barcode:
            event = False
            st['last'] += ' → barkod değil, yok sayıldı'
        elif event and query and bc == query:
            event = False
            st['last'] += ' → arama metni, yok sayıldı'

        # EAN-8/UPC-A/EAN-13 with a valid check digit is a product code
        is_ean = False
        if bc.isdigit() and len(bc) in (8, 12, 13):
            digits = [int(ch) for ch in bc.zfill(13)]
            total = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits[:12]))
            is_ean = (10 - total % 10) % 10 == digits[12]
        if prefixes:
            is_order = any(bc.startswith(p) for p in prefixes)
        else:
            is_order = len(bc) >= min_len and not (ean_on and is_ean)

        if event:
            if is_order and st['rec'] and bc == st['bc']:
                st['last'] += ' → aynı sipariş, kayıt sürüyor'
            elif is_order:
                safe = re.sub(r'[^A-Za-z0-9_-]', '_', bc)[:60]
                st['pending'] = (safe + '_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), bc)
                if st['rec']:
                    st['rec'] = False
                    st['gap_until'] = now + FINALIZE_GAP
                    st['status'] = 'Önceki kayıt kapatılıyor'
            elif st['rec']:
                st['items'].append(bc)
                st['last'] += ' → ürün'
            else:
                st['status'] = 'Ürün barkodu okundu, açık sipariş yok: ' + bc

        if st['rec'] and now - st['start'] >= max_s:
            st['rec'] = False
            st['gap_until'] = now + FINALIZE_GAP
            st['status'] = 'Kayıt tamamlandı: ' + st['bc']

        if st['pending'] and not st['rec'] and now >= st['gap_until']:
            name, code = st['pending']
            st['pending'] = None
            st.update(rec=True, name=name, bc=code, start=now, items=[])

        remaining = max(0.0, max_s - (now - st['start'])) if st['rec'] else 0.0
        ts = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        if st['rec']:
            overlay = st['bc'] + '  |  ' + ts + '  |  ' + station
            if st['items']:
                overlay += '  |  urun: ' + str(len(st['items']))
            st['status'] = 'Kaydediliyor: ' + st['bc'] + ' (' + str(int(remaining)) + ' sn)'
        else:
            overlay = ts + '  |  ' + station + '  |  barkod bekleniyor'

        outputs['Record'] = bool(st['rec'])
        outputs['File Name'] = st['name']
        outputs['Overlay Text'] = overlay
        outputs['Active Barcode'] = st['bc'] if st['rec'] else ''
        outputs['Remaining'] = float(remaining)
        outputs['Status'] = st['status'] + ('  ·  ' + st['last'] if st['last'] else '')
        outputs['Products'] = len(st['items']) if st['rec'] else 0
        outputs['Max Seconds'] = max_s
        outputs['Station'] = station

    def run(self):
        inputs = {
            'Barcode': self.input['Barcode'].data,
            'Scan': self.input['Scan'].data,
            'Folder': self.input['Folder'].data,
            'Search Query': self.input['Search Query'].data
        }
        parameters = {
            'max_seconds': float(self.param['max_seconds'].value),
            'min_length': int(self.param['min_length'].value),
            'prefixes': str(self.param['prefixes'].value),
            'station': str(self.param['station'].value),
            'ean_products': bool(self.param['ean_products'].is_checked)
        }
        state = self._augelab_generated_state
        outputs = {
            'Record': None,
            'File Name': None,
            'Overlay Text': None,
            'Active Barcode': None,
            'Remaining': None,
            'Status': None,
            'Products': None,
            'Max Seconds': None,
            'Station': None
        }
        self._process(inputs, parameters, state, outputs)
        unknown = set(outputs).difference(self._augelab_output_names)
        if unknown:
            raise ValueError(f"Undeclared generated outputs: {sorted(unknown)}")
        for output_name in self._augelab_output_names:
            self.output[output_name].data = outputs[output_name]


add_block(PaketKayitKontrol.op_code, PaketKayitKontrol)
