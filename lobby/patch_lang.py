# -*- coding: utf-8 -*-
"""大厅语言设置: 默认中文+持久化选择器; 跳转游戏带 lang。"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1) lobby main.js default lang
p = r'D:\pslobby_wc\trunk\main.js'
d = open(p, encoding='utf-8').read()
old = 'var lan = "eng";'
new = 'var lan = (window.localStorage && localStorage.getItem("ps_lang")) || "sch";'
if old in d:
    d = d.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('main.js default lang -> localStorage||sch')

# 2) core.js: GetLang helper + append lang to launch urls
p = r'D:\pslobby_wc\trunk\src\core.js'
d = open(p, encoding='utf-8').read()
if 'pslb.GetLang' not in d:
    helper = ('pslb.GetLang = function(){ var m = window.location.search.match(/[?&]lang=([^&]+)/); '
              'if (m) return m[1]; return (window.localStorage && localStorage.getItem("ps_lang")) || "sch"; };\n')
    d = d.replace('pslb.BuildWebSocket = function', helper + 'pslb.BuildWebSocket = function', 1)
    d = d.replace('?access_token=dev&subid=" + subgame_id;', '?access_token=dev&subid=" + subgame_id + "&lang=" + pslb.GetLang();')
    open(p, 'w', encoding='utf-8').write(d)
    print('core.js GetLang + launch lang appended')

# 3) index.html overlay language selector
p = r'D:\pslobby_wc\trunk\index.html'
d = open(p, encoding='utf-8').read()
if 'ps-lang-panel' not in d:
    overlay = '''
<div id="ps-lang-btn" style="position:fixed;top:8px;right:8px;z-index:9999;background:#2b2b3b;color:#fff;border:1px solid #666;border-radius:6px;padding:6px 10px;font:14px sans-serif;cursor:pointer;">🌐 语言</div>
<div id="ps-lang-panel" style="display:none;position:fixed;top:44px;right:8px;z-index:9999;background:#2b2b3b;color:#fff;border:1px solid #666;border-radius:6px;padding:10px;font:14px sans-serif;">
  <div style="margin-bottom:6px;">选择语言 / Language</div>
  <select id="ps-lang-select" style="font:14px sans-serif;padding:4px;">
    <option value="sch">简体中文</option><option value="tch">繁體中文</option><option value="eng">English</option>
    <option value="tai">ไทย</option><option value="vie">Tiếng Việt</option><option value="kor">한국어</option>
    <option value="ind">Indonesia</option><option value="mys">Melayu</option><option value="esp">Español</option>
  </select>
  <button id="ps-lang-apply" style="margin-left:6px;font:14px sans-serif;padding:4px 10px;cursor:pointer;">应用</button>
</div>
<script>
(function(){
  var cur = (window.localStorage && localStorage.getItem("ps_lang")) || "sch";
  var sel = document.getElementById("ps-lang-select"); sel.value = cur;
  document.getElementById("ps-lang-btn").onclick = function(){
    var p = document.getElementById("ps-lang-panel"); p.style.display = (p.style.display === "none") ? "block" : "none";
  };
  document.getElementById("ps-lang-apply").onclick = function(){
    var v = sel.value; localStorage.setItem("ps_lang", v);
    var u = new URL(window.location.href); u.searchParams.set("lang", v); window.location.href = u.toString();
  };
})();
</script>
'''
    d = d.replace('</body>', overlay + '</body>', 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('index.html language selector injected')