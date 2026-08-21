# -*- coding: utf-8 -*-
"""
يسحب آخر الأخبار من التغذيات الرسمية (RSS/Atom) ويكتب news.json.

مبدأ التصميم: لا يُفسد الملف أبداً.
- إن فشل مصدر، نتخطّاه ونُبقي أخباره السابقة.
- إن فشلت كل المصادر، نُبقي news.json كما هو ونخرج بنجاح
  (حتى لا تتحوّل الصفحة إلى فارغة بسبب عطل شبكة مؤقّت).
"""
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS = os.path.join(ROOT, 'news.json')

# مصادر آلية: تحقّقنا أن هاتين التغذيتين تعملان فعلاً.
# Anthropic وMiniMax لا تنشران RSS رسمياً، فأخبارهما تُدار يدوياً في curated.json.
FEEDS = [
    ('ChatGPT', 'https://openai.com/news/rss.xml',          'https://openai.com/news/'),
    ('Qwen',    'https://qwenlm.github.io/blog/index.xml',  'https://qwenlm.github.io/blog/'),
]

CURATED_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'curated.json')
CURATED_ORDER = ['Claude', 'MiniMax']   # ترتيب ظهورها ضمن القائمة

PER_TOOL = 2          # عدد الأخبار لكل أداة
TIMEOUT = 25
UA = 'Mozilla/5.0 (compatible; watnia-ai-guide/1.0; +https://ai.watnia.com)'


def strip_html(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&')
          .replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"'))
    return re.sub(r'\s+', ' ', s).strip()


def shorten(s, limit=190):
    s = strip_html(s)
    return s if len(s) <= limit else s[:limit].rstrip() + '…'


def tag(el):
    """اسم الوسم بلا namespace."""
    return el.tag.split('}')[-1] if '}' in el.tag else el.tag


def parse_date(raw):
    if not raw:
        return ''
    raw = raw.strip()
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
        try:
            return datetime.strptime(raw, fmt).strftime('%Y-%m')
        except ValueError:
            continue
    m = re.search(r'(\d{4})-(\d{2})', raw)
    return f'{m.group(1)}-{m.group(2)}' if m else ''


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def entries_from(xml_bytes, tool, fallback_url):
    root = ET.fromstring(xml_bytes)
    nodes = [e for e in root.iter() if tag(e) in ('item', 'entry')]
    out = []
    for node in nodes[:PER_TOOL]:
        title = link = summary = date_raw = ''
        for child in node:
            t = tag(child)
            if t == 'title':
                title = strip_html(child.text or '')
            elif t == 'link':
                link = (child.get('href') or child.text or '').strip()
            elif t in ('description', 'summary', 'content'):
                if not summary:
                    summary = shorten(child.text or '')
            elif t in ('pubDate', 'published', 'updated'):
                if not date_raw:
                    date_raw = child.text or ''
        if not title:
            continue
        out.append({
            'tool': tool,
            'date': parse_date(date_raw),
            'title': shorten(title, 110),
            'summary': summary or 'اطّلع على التفاصيل في المصدر الرسمي.',
            'url': link or fallback_url,
        })
    return out


def main():
    try:
        with open(NEWS, encoding='utf-8') as f:
            current = json.load(f)
    except Exception:
        current = {'items': []}

    previous = current.get('items', [])
    collected, failed = [], []

    # 1) الأخبار المُدارة يدوياً (أدوات بلا RSS رسمي)
    try:
        with open(CURATED_FILE, encoding='utf-8') as f:
            curated = json.load(f)
        for tool in CURATED_ORDER:
            for item in curated.get(tool, [])[:PER_TOOL]:
                collected.append({
                    'tool': tool,
                    'date': item.get('date', ''),
                    'title': item.get('title', ''),
                    'summary': item.get('summary', ''),
                    'url': item.get('url', ''),
                })
        print(f'CURATED: {len(collected)} item(s)')
    except Exception as e:
        print(f'FAIL curated.json: {e}', file=sys.stderr)

    # 2) الأخبار الآلية من التغذيات
    for tool, feed_url, fallback in FEEDS:
        try:
            got = entries_from(fetch(feed_url), tool, fallback)
            if got:
                collected.extend(got)
                print(f'OK   {tool}: {len(got)} item(s)')
            else:
                raise ValueError('no entries parsed')
        except Exception as e:
            failed.append(tool)
            print(f'FAIL {tool}: {e}', file=sys.stderr)
            # أبقِ أخبار هذه الأداة من الملف السابق
            kept = [i for i in previous if i.get('tool') == tool][:PER_TOOL]
            collected.extend(kept)
            if kept:
                print(f'     kept {len(kept)} previous item(s) for {tool}')

    if not collected:
        print('لم يُجلب أي خبر ولا توجد أخبار سابقة — أُبقي الملف كما هو.', file=sys.stderr)
        return 0

    data = {
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'source': 'auto' if not failed else f'auto (تعذّر: {", ".join(failed)})',
        'note': 'يُحدَّث تلقائياً أسبوعياً عبر GitHub Action من المدوّنات الرسمية.',
        'items': collected,
    }
    with open(NEWS, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'تم: {len(collected)} خبر | تعذّر: {failed or "لا شيء"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
