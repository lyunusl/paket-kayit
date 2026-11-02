# Paket Kayıt - Developed by AugeLab
# Copyright (c) 2026 AugeLab. Licensed under the MIT License (see LICENSE).

from studio.custom_block import (
    Block, CheckBox, DropDown, Label, SocketTypes, TextInput, add_block,
)

import sys
import threading
import http.server
import json
import os
import re
import time
import datetime
import urllib.parse
import cv2
import webbrowser

class PaketWebArayuz(Block):
    op_code = 'PaketWebArayuz'
    input_sockets = [
        SocketTypes.ImageAny('Frame', multiple=False),
        SocketTypes.String('Status', multiple=False),
        SocketTypes.Number('Remaining', multiple=False),
        SocketTypes.String('Active Barcode', multiple=False),
        SocketTypes.Integer('Products', multiple=False),
        SocketTypes.Number('Max Seconds', multiple=False),
        SocketTypes.String('Station', multiple=False),
        SocketTypes.String('Camera Status', multiple=False),
        SocketTypes.String('Folder', multiple=False),
        SocketTypes.String('Page', multiple=False)
    ]
    output_sockets = [
        SocketTypes.String('URL', multiple=False),
        SocketTypes.String('Server Status', multiple=False)
    ]
    _augelab_generated_spec_version = 1
    _augelab_output_names = ('URL', 'Server Status')

    def init(self):
        self.op_title = 'Paket Web Arayüzü'
        self.width = 280
        self.height = 240
        self.tooltip = 'Runs the Paket Kayıt web server on http://127.0.0.1:<port>/ (or the LAN when allowed): serves the page from Paket Web Sayfası, live view, state, scan input, recording search, playback and download. The server keeps running in Studio.'
        self.param['label:port'] = Label(text='Arayüz portu')
        self.param['port'] = TextInput(name='port', text='8080')
        self.param['allow_network'] = CheckBox(name='allow_network', text='Yerel ağdan erişime izin ver', init_state=False)
        self.param['open_browser'] = CheckBox(name='open_browser', text='Başlayınca tarayıcıyı aç', init_state=True)
        self._augelab_generated_state = {}

    @staticmethod
    def _process(inputs, parameters, state, outputs):
        VERSION = 4
        now = time.time()
        g = sys.__dict__.setdefault('_paket_kayit_web', {})
        port = int(parameters['port'] or 8080)
        web = g.setdefault(port, {'jpeg': None, 'state': {}, 'scans': [], 'folder': '', 'lock': threading.Lock()})
        web['folder'] = str(inputs['Folder'] or '').strip()

        # a server left by an older version of this block keeps serving old pages; replace it
        if 'server' in web and web.get('version') != VERSION:
            try:
                web['server'].shutdown()
                web['server'].server_close()
            except Exception:
                pass
            del web['server']

        if 'server' not in web and now >= web.get('retry_at', 0):
            PAT = re.compile(r'^(.+)_(\d{8})_(\d{6})\.mp4$')

            class Handler(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def _send(self, code, body, ctype):
                    self.send_response(code)
                    self.send_header('Content-Type', ctype)
                    self.send_header('Content-Length', str(len(body)))
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(body)

                def _json(self, code, obj):
                    self._send(code, json.dumps(obj, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')

                def _records(self, q):
                    folder = web['folder']
                    out = []
                    if folder and os.path.isdir(folder):
                        for f in os.listdir(folder):
                            m = PAT.match(f)
                            if not m or (q and q.lower() not in m.group(1).lower()):
                                continue
                            try:
                                size = os.path.getsize(os.path.join(folder, f))
                            except OSError:
                                continue
                            if size == 0:
                                continue
                            d, t = m.group(2), m.group(3)
                            out.append({'file': f, 'barcode': m.group(1), 'date': d[6:8] + '.' + d[4:6] + '.' + d[:4], 'time': t[:2] + ':' + t[2:4] + ':' + t[4:], 'key': d + t, 'mb': round(size / 1048576.0, 1)})
                    out.sort(key=lambda r: r['key'], reverse=True)
                    return out[:200]

                def _file(self, name, attach):
                    if not PAT.match(name) or os.path.basename(name) != name:
                        return self._send(404, b'not found', 'text/plain')
                    fp = os.path.join(web['folder'], name)
                    if not os.path.isfile(fp):
                        return self._send(404, b'not found', 'text/plain')
                    size = os.path.getsize(fp)
                    start, end = 0, size - 1
                    m = re.match(r'bytes=(\d*)-(\d*)', self.headers.get('Range') or '')
                    if m and (m.group(1) or m.group(2)):
                        if m.group(1):
                            start = int(m.group(1))
                            if m.group(2):
                                end = min(int(m.group(2)), size - 1)
                        else:
                            start = max(0, size - int(m.group(2)))
                        self.send_response(206)
                        self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
                    else:
                        self.send_response(200)
                    self.send_header('Content-Type', 'video/mp4')
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Content-Length', str(end - start + 1))
                    if attach:
                        self.send_header('Content-Disposition', 'attachment; filename="' + name + '"')
                    self.end_headers()
                    with open(fp, 'rb') as fh:
                        fh.seek(start)
                        left = end - start + 1
                        while left > 0:
                            chunk = fh.read(min(262144, left))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            left -= len(chunk)

                def do_GET(self):
                    try:
                        u = urllib.parse.urlparse(self.path)
                        p = u.path
                        route = web.get('routes', {}).get(p)
                        if p == '/':
                            self._send(200, web.get('html', 'Sayfa yükleniyor...').encode('utf-8'), 'text/html; charset=utf-8')
                        elif route:
                            code, obj = route[0](self.client_address[0] in ('127.0.0.1', '::1'))
                            self._json(code, obj)
                        elif p == '/api/state':
                            with web['lock']:
                                body = json.dumps(web['state']).encode('utf-8')
                            self._send(200, body, 'application/json')
                        elif p == '/api/records':
                            q = urllib.parse.parse_qs(u.query).get('q', [''])[0].strip()
                            self._send(200, json.dumps(self._records(q)).encode('utf-8'), 'application/json')
                        elif p == '/stream.mjpg':
                            self.send_response(200)
                            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                            self.send_header('Cache-Control', 'no-store')
                            self.end_headers()
                            last = None
                            while web.get('server') is srv_ref[0]:
                                jpg = web['jpeg']
                                if jpg is not None and jpg is not last:
                                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(len(jpg)).encode() + b'\r\n\r\n' + jpg + b'\r\n')
                                    last = jpg
                                time.sleep(0.04)
                        elif p.startswith('/video/') or p.startswith('/download/'):
                            self._file(urllib.parse.unquote(p.split('/', 2)[2]), p.startswith('/download/'))
                        else:
                            self._send(404, b'not found', 'text/plain')
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                        pass

                def do_POST(self):
                    try:
                        n = int(self.headers.get('Content-Length') or 0)
                        data = json.loads(self.rfile.read(min(n, 16384)) or b'{}')
                        route = web.get('routes', {}).get(self.path)
                        if self.path == '/api/scan':
                            code = str(data.get('code', '')).strip()[:64]
                            if code:
                                with web['lock']:
                                    web['scans'].append(code)
                            self._json(200, {'ok': True})
                        elif route:
                            code, obj = route[1](data, self.client_address[0] in ('127.0.0.1', '::1'))
                            self._json(code, obj)
                        else:
                            self._send(404, b'not found', 'text/plain')
                    except Exception as e:
                        self._json(400, {'ok': False, 'error': 'Geçersiz istek: ' + str(e)})

            srv_ref = [None]
            host = '0.0.0.0' if parameters['allow_network'] else '127.0.0.1'
            try:
                srv = http.server.ThreadingHTTPServer((host, port), Handler)
                srv.daemon_threads = True
                srv_ref[0] = srv
                threading.Thread(target=srv.serve_forever, daemon=True).start()
                web['server'] = srv
                web['version'] = VERSION
                web['err'] = ''
                if parameters['open_browser'] and not web.get('opened'):
                    web['opened'] = True
                    webbrowser.open('http://127.0.0.1:%d/' % port)
            except OSError as e:
                web['err'] = 'Port ' + str(port) + ' açılamadı: ' + str(e)
                web['retry_at'] = now + 5

        frame = inputs['Frame']
        if frame is not None and now - web.get('jpeg_t', 0) >= 0.08:
            ok, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ok:
                web['jpeg'] = enc.tobytes()
                web['jpeg_t'] = now

        if now - web.get('count_t', 0) >= 5:
            web['count_t'] = now
            today = '_' + datetime.datetime.now().strftime('%Y%m%d') + '_'
            n = 0
            try:
                for f in os.listdir(web['folder']):
                    if today in f and f.endswith('.mp4') and not f.endswith('.partial.mp4'):
                        n += 1
            except OSError:
                pass
            web['today'] = n

        status = str(inputs['Status'] or '')
        with web['lock']:
            web['state'] = {
                'ts': now,
                'status': status.split('  ·  ')[0],
                'barcode': str(inputs['Active Barcode'] or ''),
                'remaining': float(inputs['Remaining'] or 0),
                'max': float(inputs['Max Seconds'] or 0),
                'products': int(inputs['Products'] or 0),
                'station': str(inputs['Station'] or ''),
                'camera': str(inputs['Camera Status'] or ''),
                'today': web.get('today', 0),
                'beep': web.get('beep', 0),
                'last_code': web.get('last_code', ''),
            }
        url = 'http://127.0.0.1:' + str(port) + '/'
        outputs['URL'] = url if 'server' in web else ''
        outputs['Server Status'] = web.get('err') or ('Arayüz açık: ' + url)

    def run(self):
        inputs = {
            'Frame': self.input['Frame'].data,
            'Status': self.input['Status'].data,
            'Remaining': self.input['Remaining'].data,
            'Active Barcode': self.input['Active Barcode'].data,
            'Products': self.input['Products'].data,
            'Max Seconds': self.input['Max Seconds'].data,
            'Station': self.input['Station'].data,
            'Camera Status': self.input['Camera Status'].data,
            'Folder': self.input['Folder'].data,
            'Page': self.input['Page'].data
        }
        parameters = {
            'port': int(self.param['port'].value),
            'allow_network': bool(self.param['allow_network'].is_checked),
            'open_browser': bool(self.param['open_browser'].is_checked)
        }
        state = self._augelab_generated_state
        outputs = {
            'URL': None,
            'Server Status': None
        }
        self._process(inputs, parameters, state, outputs)
        unknown = set(outputs).difference(self._augelab_output_names)
        if unknown:
            raise ValueError(f"Undeclared generated outputs: {sorted(unknown)}")
        for output_name in self._augelab_output_names:
            self.output[output_name].data = outputs[output_name]


add_block(PaketWebArayuz.op_code, PaketWebArayuz)
