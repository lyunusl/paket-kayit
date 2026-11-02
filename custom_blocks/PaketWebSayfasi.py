# Paket Kayıt - Developed by AugeLab
# Copyright (c) 2026 AugeLab. Licensed under the MIT License (see LICENSE).

from studio.custom_block import (
    Block, CheckBox, DropDown, Label, SocketTypes, TextInput, add_block,
)

import sys
import threading
import json
import os

class PaketWebSayfasi(Block):
    op_code = 'PaketWebSayfasi'
    input_sockets = [
        
    ]
    output_sockets = [
        SocketTypes.String('Page', multiple=False)
    ]
    _augelab_generated_spec_version = 1
    _augelab_output_names = ('Page',)

    def init(self):
        self.op_title = 'Paket Web Sayfası'
        self.width = 280
        self.height = 180
        self.tooltip = 'Provides the Paket Kayıt web page and its settings API to the Paket Web Arayüzü server. Settings are saved to %APPDATA%/PaketKayit/ayarlar.json and can be changed only from this PC.'
        self.param['label:port'] = Label(text='Arayüz portu')
        self.param['port'] = TextInput(name='port', text='8080')
        self._augelab_generated_state = {}

    @staticmethod
    def _process(inputs, parameters, state, outputs):
        PAGE_VERSION = 1
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
        g = sys.__dict__.setdefault('_paket_kayit_web', {})
        port = int(parameters['port'] or 8080)
        web = g.setdefault(port, {'jpeg': None, 'state': {}, 'scans': [], 'folder': '', 'lock': threading.Lock()})
        if web.get('page_version') == PAGE_VERSION:
            outputs['Page'] = 'ok'
            return

        web['html'] = r'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>Paket Kayıt</title>
        <style>
        :root{--bg:#0b0d10;--panel:#14171c;--panel2:#1b1f26;--line:#252a31;--text:#eef0f3;--muted:#8a94a3;--acc:#fde035;--rec:#ff4d3d;--ok:#3ddc84}
        *{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font:15px/1.45 "Segoe UI",system-ui,-apple-system,sans-serif}
        header{display:flex;align-items:center;gap:14px;padding:14px 24px;border-bottom:1px solid var(--line)}
        .brand{font-weight:700;font-size:19px;margin-right:6px}.brand b{color:var(--acc)}
        .pill{padding:5px 12px;border:1px solid var(--line);border-radius:99px;color:var(--muted);font-size:13px;white-space:nowrap}
        .dot{width:8px;height:8px;border-radius:50%;background:var(--muted);display:inline-block;margin-right:7px;vertical-align:1px}
        nav{margin-left:auto;display:flex;gap:4px;background:var(--panel);padding:4px;border-radius:10px}
        nav button{background:none;border:0;color:var(--muted);font:inherit;font-weight:600;padding:7px 18px;border-radius:7px;cursor:pointer;outline:none}
        nav button.on{background:var(--panel2);color:var(--text)}
        #clock{font-variant-numeric:tabular-nums;color:var(--muted);min-width:70px;text-align:right}
        main{padding:20px 24px;display:none}main.on{display:grid}
        #pack{grid-template-columns:minmax(0,1fr) 360px;gap:20px}
        .live{position:relative;background:#000;border-radius:16px;overflow:hidden;aspect-ratio:16/9;border:1px solid var(--line);transition:box-shadow .15s}
        .live.flash{box-shadow:0 0 0 4px var(--ok)}
        .live img{width:100%;height:100%;object-fit:contain;display:block;transition:opacity .3s}
        .badge{position:absolute;top:16px;right:16px;padding:7px 14px;border-radius:9px;font-weight:700;font-size:13px;letter-spacing:1px;background:rgba(0,0,0,.65);color:var(--muted)}
        .badge.rec{background:var(--rec);color:#fff}.badge.rec::before{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;background:#fff;margin-right:9px;animation:bl 1s infinite}
        @keyframes bl{50%{opacity:.15}}
        .bar{height:6px;background:var(--line);border-radius:99px;margin-top:14px;overflow:hidden}.bar i{display:block;height:100%;width:0;background:var(--acc);transition:width .5s linear}
        .side{display:flex;flex-direction:column;gap:16px;min-width:0}
        .card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 20px;min-width:0}
        .card h3{margin:0 0 10px;font-size:12px;letter-spacing:1.3px;text-transform:uppercase;color:var(--muted);font-weight:600}
        .code{font:600 30px/1.2 Consolas,"Cascadia Mono",monospace;word-break:break-all}
        .code.idle{color:var(--muted);font:500 18px/1.4 "Segoe UI",system-ui,sans-serif}
        .meta{color:var(--muted);margin-top:8px;font-size:13px}
        .big{font-size:48px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
        .list{list-style:none;margin:0;padding:0;overflow-x:hidden}.list li{display:flex;justify-content:space-between;gap:10px;padding:9px 10px;border-radius:9px;cursor:pointer;min-width:0}
        .list li:hover,.list li.sel{background:var(--panel2)}.list .c{font-family:Consolas,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}.list .t{color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:13px;flex:none}
        .list li.empty{color:var(--muted);cursor:default;justify-content:center;padding:28px 0}.list li.empty:hover{background:none}
        #focus{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--acc);color:#111;font-weight:700;padding:13px 24px;border-radius:12px;display:none;cursor:pointer;box-shadow:0 10px 30px rgba(0,0,0,.5)}
        #toast{position:fixed;top:78px;left:50%;transform:translateX(-50%);background:var(--ok);color:#06210f;font:700 18px Consolas,monospace;padding:12px 24px;border-radius:12px;opacity:0;transition:opacity .2s;pointer-events:none;box-shadow:0 10px 30px rgba(0,0,0,.5)}
        #arch{grid-template-columns:380px minmax(0,1fr);gap:20px}
        input[type=search]{width:100%;background:var(--bg);border:1px solid var(--line);color:var(--text);font:600 18px Consolas,monospace;padding:12px 14px;border-radius:10px;outline:none}
        input[type=search]:focus{border-color:var(--acc)}
        #results{margin-top:12px;max-height:calc(100vh - 260px);overflow-y:auto}
        video{width:100%;border-radius:16px;background:#000;aspect-ratio:16/9;border:1px solid var(--line);display:block}
        .row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px}
        .btn{background:var(--acc);color:#111;font:inherit;font-weight:700;border:0;border-radius:10px;padding:11px 22px;text-decoration:none;white-space:nowrap;cursor:pointer}
        .sgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px;align-items:start}
        .sgrid label{display:block;color:var(--muted);font-size:13px;margin-top:14px}
        .sgrid label:first-of-type{margin-top:4px}
        .sgrid input:not([type=checkbox]),.sgrid select{display:block;width:100%;margin-top:6px;background:var(--bg);border:1px solid var(--line);color:var(--text);font:15px "Segoe UI",system-ui,sans-serif;padding:10px 12px;border-radius:10px;outline:none}
        .sgrid input:focus,.sgrid select:focus{border-color:var(--acc)}
        .sgrid label.chk{display:flex;align-items:center;gap:10px;color:var(--text);font-size:14px;margin-top:16px;cursor:pointer}
        .chk input{width:18px;height:18px;accent-color:var(--acc);margin:0}
        .hint{color:var(--muted);font-size:12px;margin-top:5px}
        .savebar{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;gap:12px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 20px}
        footer{padding:8px 24px 28px;color:var(--muted);font-size:12px;text-align:right;letter-spacing:.3px}footer b{color:var(--text);font-weight:600}
        body.stale .live img{opacity:.3}
        @media (max-width:980px){#pack,#arch{grid-template-columns:1fr}header{flex-wrap:wrap}}
        </style></head><body>
        <header><div class="brand">Paket <b>Kayıt</b></div><span class="pill" id="station">—</span><span class="pill"><span class="dot" id="camdot"></span><span id="cam">Kamera</span></span>
        <nav><button class="on" data-tab="pack">Paketleme</button><button data-tab="arch">Kayıtlar</button><button data-tab="set">Ayarlar</button></nav><span id="clock"></span></header>
        <main id="pack" class="on">
        <div><div class="live" id="live"><img src="/stream.mjpg" alt=""><span class="badge" id="badge">BEKLEMEDE</span></div><div class="bar"><i id="prog"></i></div></div>
        <div class="side">
        <div class="card"><h3>Şu anki sipariş</h3><div class="code idle" id="code">Sipariş barkodunu okutun</div><div class="meta" id="meta"></div></div>
        <div class="card"><h3>Bugün paketlenen</h3><div class="big" id="today">0</div></div>
        <div class="card"><h3>Son kayıtlar</h3><ul class="list" id="recent"></ul></div>
        </div></main>
        <main id="arch">
        <div class="card"><h3>Kayıt ara</h3><input type="search" id="q" placeholder="Barkod veya bir kısmı" autocomplete="off"><ul class="list" id="results"></ul></div>
        <div><video id="player" controls></video><div class="row"><div style="min-width:0"><div class="code" id="ptitle" style="font-size:20px">Bir kayıt seçin</div><div class="meta" id="pmeta"></div></div><a class="btn" id="dl" href="#" style="display:none">İndir</a></div></div>
        </main>
        <main id="set"><form id="sf" class="sgrid" autocomplete="off">
        <div class="card"><h3>Masa ve kamera</h3>
        <label>Masa adı<input name="station" maxlength="60"></label>
        <label>Kamera numarası<input name="camera_index" type="number" min="0" max="9"></label><div class="hint">0 ilk kamera, 1 ikinci kamera.</div>
        <label>Çözünürlük<select name="resolution"><option>640 x 480</option><option>1280 x 720</option><option>1920 x 1080</option></select></label>
        <label class="chk"><input type="checkbox" name="draw_box">Barkodu kare içine al</label></div>
        <div class="card"><h3>Kayıt</h3>
        <label>Kayıt klasörü<input name="folder" maxlength="200"></label>
        <label>Azami kayıt süresi (sn)<input name="max_seconds" type="number" min="5" max="600"></label><div class="hint">Bir sonraki sipariş barkodu gelmezse kayıt bu sürede biter.</div>
        <label>Saklama süresi (gün)<input name="keep_days" type="number" min="0" max="3650"></label><div class="hint">Daha eski kayıtlar silinir. 0 yazılırsa hiç silinmez.</div></div>
        <div class="card"><h3>Barkod kuralları</h3>
        <label>Sipariş barkodu önekleri<input name="prefixes" maxlength="200" placeholder="Örn. TY, 7270"></label><div class="hint">Virgülle ayırın. Boş bırakılırsa uzunluk kuralı kullanılır.</div>
        <label>Sipariş barkodu en az uzunluk<input name="min_length" type="number" min="1" max="64"></label>
        <label class="chk"><input type="checkbox" name="ean_products">EAN/UPC barkodlarını ürün say</label>
        <label>Aynı barkodu yeniden sayma süresi (sn)<input name="cooldown" type="number" min="0.5" max="120" step="0.5"></label></div>
        <div class="savebar"><span class="meta" id="smsg" style="margin:0">Ayarlar bu bilgisayarda saklanır ve hemen uygulanır.</span><button class="btn" type="submit">Kaydet</button></div>
        </form></main>
        <footer>Paket Kayıt · Developed by <b>AugeLab</b></footer>
        <div id="focus">Barkod okutmak ve sesli uyarı için sayfaya tıklayın</div><div id="toast"></div>
        <script>
        const $=id=>document.getElementById(id);let tab='pack',buf='',bt=0,sel='',lastBeep=null,actx=null;
        function audio(){try{actx=actx||new (window.AudioContext||window.webkitAudioContext)();if(actx.state==='suspended')actx.resume()}catch(e){}}
        function beep(){audio();if(!actx)return;const t=actx.currentTime,o=actx.createOscillator(),g=actx.createGain();o.type='square';o.frequency.value=1700;g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(0.2,t+0.01);g.gain.exponentialRampToValueAtTime(0.0001,t+0.16);o.connect(g);g.connect(actx.destination);o.start(t);o.stop(t+0.17)}
        document.addEventListener('pointerdown',audio);document.addEventListener('keydown',audio);
        function show(t){tab=t;document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.tab===t));document.querySelectorAll('main').forEach(m=>m.classList.toggle('on',m.id===t));if(t==='arch')search();else if(t==='set')loadSettings();else document.activeElement.blur()}
        document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>show(b.dataset.tab));
        function row(r){const li=document.createElement('li');li.innerHTML='<span class="c"></span><span class="t"></span>';li.firstChild.textContent=r.barcode;li.lastChild.textContent=r.date+' '+r.time;li.dataset.file=r.file;if(r.file===sel)li.classList.add('sel');li.onclick=()=>play(r);return li}
        function empty(ul,m){ul.innerHTML='';const li=document.createElement('li');li.className='empty';li.textContent=m;ul.appendChild(li)}
        function play(r){sel=r.file;if(tab!=='arch')show('arch');document.querySelectorAll('#results li').forEach(x=>x.classList.toggle('sel',x.dataset.file===sel));const v=$('player');v.src='/video/'+encodeURIComponent(r.file);v.play().catch(()=>{});$('ptitle').textContent=r.barcode;$('pmeta').textContent=r.date+' '+r.time+' · '+r.mb+' MB';$('dl').href='/download/'+encodeURIComponent(r.file);$('dl').style.display=''}
        async function records(q){return (await fetch('/api/records?q='+encodeURIComponent(q||''))).json()}
        async function search(){try{const rs=await records($('q').value.trim());const ul=$('results');if(!rs.length)return empty(ul,'Kayıt bulunamadı');ul.innerHTML='';rs.forEach(r=>ul.appendChild(row(r)))}catch(e){}}
        let st;$('q').oninput=()=>{clearTimeout(st);st=setTimeout(search,250)};
        async function recent(){try{const rs=await records('');const ul=$('recent');if(!rs.length)return empty(ul,'Henüz kayıt yok');ul.innerHTML='';rs.slice(0,8).forEach(r=>ul.appendChild(row(r)))}catch(e){}}
        function toast(m){const t=$('toast');t.textContent=m;t.style.opacity=1;clearTimeout(t._h);t._h=setTimeout(()=>t.style.opacity=0,1500)}
        async function loadSettings(){try{const s=await (await fetch('/api/settings')).json();for(const el of $('sf').elements){if(!el.name||!(el.name in s))continue;if(el.type==='checkbox')el.checked=!!s[el.name];else el.value=s[el.name]}if(s._readonly){$('smsg').textContent='Ayarlar sadece Studio’nun çalıştığı bilgisayardan değiştirilebilir.'}}catch(e){$('smsg').textContent='Ayarlar alınamadı'}}
        $('sf').onsubmit=async e=>{e.preventDefault();const d={};for(const el of $('sf').elements){if(!el.name)continue;d[el.name]=el.type==='checkbox'?el.checked:(el.type==='number'?Number(el.value):el.value)}try{const j=await (await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)})).json();if(j.ok){toast('Ayarlar kaydedildi');$('smsg').textContent='Kaydedildi · '+new Date().toLocaleTimeString('tr-TR')}else $('smsg').textContent=j.error||'Kaydedilemedi'}catch(err){$('smsg').textContent='Bağlantı yok'}};
        async function poll(){try{const s=await (await fetch('/api/state')).json();const live=s.ts&&Date.now()/1000-s.ts<3;document.body.classList.toggle('stale',!live);$('station').textContent=s.station||'—';$('cam').textContent=live?(s.camera||'Kamera'):'Sahne çalışmıyor';$('camdot').style.background=live&&(s.camera||'').indexOf('·')>0?'var(--ok)':'var(--rec)';
        if(typeof s.beep==='number'){if(lastBeep!==null&&s.beep>lastBeep){beep();toast('Okundu: '+(s.last_code||''));const l=$('live');l.classList.add('flash');setTimeout(()=>l.classList.remove('flash'),500)}lastBeep=s.beep}
        const rec=live&&!!s.barcode;const b=$('badge');b.className='badge'+(rec?' rec':'');b.textContent=rec?'KAYIT':(live?'BEKLEMEDE':'DURDU');
        $('code').textContent=rec?s.barcode:'Sipariş barkodunu okutun';$('code').className='code'+(rec?'':' idle');
        $('meta').textContent=rec?(Math.ceil(s.remaining)+' sn kaldı · '+s.products+' ürün okundu'):(live?(s.status||''):'');
        $('prog').style.width=(rec&&s.max?Math.min(100,100*(1-s.remaining/s.max)):0)+'%';$('today').textContent=s.today||0}catch(e){document.body.classList.add('stale');$('cam').textContent='Bağlantı yok'}}
        setInterval(poll,300);setInterval(recent,4000);poll();recent();
        setInterval(()=>{$('clock').textContent=new Date().toLocaleTimeString('tr-TR');$('focus').style.display=(tab==='pack'&&!document.hasFocus())?'block':'none'},250);
        document.addEventListener('keydown',e=>{if(tab!=='pack'||e.target.tagName==='INPUT'||e.target.tagName==='SELECT')return;const t=Date.now();if(t-bt>1500)buf='';bt=t;if(e.key==='Enter'){const c=buf.trim();buf='';if(c)fetch('/api/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:c})});e.preventDefault()}else if(e.key.length===1)buf+=e.key});
        $('focus').onclick=()=>{window.focus();audio()};
        </script></body></html>'''

        LIMITS = {'camera_index': (int, 0, 9, 'Kamera numarası'), 'max_seconds': (float, 5, 600, 'Azami kayıt süresi'), 'min_length': (int, 1, 64, 'En az uzunluk'), 'cooldown': (float, 0.5, 120, 'Yeniden sayma süresi'), 'keep_days': (int, 0, 3650, 'Saklama süresi')}
        RESOLUTIONS = ('640 x 480', '1280 x 720', '1920 x 1080')

        def merged():
            m = dict(cfg.get('defaults', {}))
            m.update(cfg.get('data', {}))
            return m

        def get_settings(local):
            s = merged()
            s['_readonly'] = not local
            return 200, s

        def post_settings(d, local):
            if not local:
                return 403, {'ok': False, 'error': 'Ayarlar sadece Studio’nun çalıştığı bilgisayardan değiştirilebilir'}
            clean = {}
            for k, v in dict(d).items():
                if k in LIMITS:
                    typ, lo, hi, label = LIMITS[k]
                    try:
                        v = typ(v)
                    except (TypeError, ValueError):
                        return 400, {'ok': False, 'error': label + ' bir sayı olmalı'}
                    if not lo <= v <= hi:
                        return 400, {'ok': False, 'error': label + ' ' + str(lo) + ' ile ' + str(hi) + ' arasında olmalı'}
                elif k in ('ean_products', 'draw_box'):
                    v = bool(v)
                elif k == 'resolution':
                    if v not in RESOLUTIONS:
                        return 400, {'ok': False, 'error': 'Geçersiz çözünürlük'}
                elif k in ('station', 'prefixes', 'folder'):
                    v = str(v).strip()[:200]
                else:
                    continue
                clean[k] = v
            if 'folder' in clean:
                if not clean['folder']:
                    return 400, {'ok': False, 'error': 'Kayıt klasörü boş olamaz'}
                try:
                    os.makedirs(clean['folder'], exist_ok=True)
                except OSError as e:
                    return 400, {'ok': False, 'error': 'Kayıt klasörü oluşturulamadı: ' + str(e)}
            new = dict(cfg['data'])
            new.update(clean)
            os.makedirs(os.path.dirname(cfg['path']), exist_ok=True)
            with open(cfg['path'], 'w', encoding='utf-8') as fh:
                json.dump(new, fh, ensure_ascii=False, indent=2)
            cfg['data'].update(clean)
            return 200, {'ok': True, 'settings': merged()}

        web['routes'] = {'/api/settings': (get_settings, post_settings)}
        web['page_version'] = PAGE_VERSION
        outputs['Page'] = 'ok'

    def run(self):
        inputs = {
            
        }
        parameters = {
            'port': int(self.param['port'].value)
        }
        state = self._augelab_generated_state
        outputs = {
            'Page': None
        }
        self._process(inputs, parameters, state, outputs)
        unknown = set(outputs).difference(self._augelab_output_names)
        if unknown:
            raise ValueError(f"Undeclared generated outputs: {sorted(unknown)}")
        for output_name in self._augelab_output_names:
            self.output[output_name].data = outputs[output_name]


add_block(PaketWebSayfasi.op_code, PaketWebSayfasi)
