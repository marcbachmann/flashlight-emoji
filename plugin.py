def appearance():
    import Foundation
    dark_mode = Foundation.NSUserDefaults.standardUserDefaults().persistentDomainForName_(Foundation.NSGlobalDomain).objectForKey_("AppleInterfaceStyle") == "Dark"
    return "dark" if dark_mode else "light"


def score(query, field):
    if field == query:
        return 1
    s = 0
    for word in query.split(" "):
        if word == field:
            s += 0.1
        elif word in field:
            s += 0.01
    return s


def strip_accents(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s)
               if unicodedata.category(c) != 'Mn')


def normalize(s):
    s = s.lower()
    if type(s) == unicode:
        return strip_accents(s)
    else:
        return s


def find_emojis(query, emoji_arr):
    normalized_query = normalize(query)
    scored_matches = []
    others = []
    field_weights = {"aliases": 2.5, "tags": 2, "description": 1.5}
    for item in emoji_arr:
        s = 0
        for field_name, field in item.iteritems():
            weight = field_weights.get(field_name, 0)
            if weight == 0: continue
            if field_name == 'aliases': field = ' '.join(map(str,field))
            if field_name == 'tags': field = ' '.join(map(str,field))
            s += weight * score(query.lower(), field.lower()) * 0.1 # perfect word match
            s += weight * score(query, field) * 0.1 # perfect word match
            s += weight * score(normalized_query, normalize(field))
        if s:
            item.update({'score': s})
            scored_matches.append(item)
        else:
            others.append(item)

    scored_matches.sort(key=lambda k: k['score'], reverse = True)

    return {
        "matches": scored_matches,
        "others": others
    }


def build_html(appearance, content):
    html = """
    <html>
    <head>
        <style>
            body{
                padding: 10px 12px;
                font: 15px/1.4 'Helvetica Neue';
                font-weight: 300;
                -webkit-user-select: none;
            }

            h1 {
                font-size: 20px;
                font-weight: 300;
            }

            h1 small {
                margin-left: 5px;
                color: rgb(119,119,119);
            }

            .emojis {
                margin: 0 -5px 30px;
                font-size: 2.2em;
            }

            .emoji {
                display: inline-block;
                width: 40px;
                height: 60px;
                padding: 5px;
                margin-bottom: 10px;
                text-align: center;
            }

            .emoji i {
                -webkit-user-select: all;
                font-style: normal;
            }

            label, small {
                font-size: 12px;
                overflow: hidden;
                white-space: nowrap;
            }

            label {
                display: block;
                font-size: 11px;
                -webkit-user-select: all;
            }

            .dark {
                color: rgb(224,224,224);
            }
        </style>
    </head>
    <script>
        function copyToClipboard(emoji) {
            command = 'printf "{{emoji}}" | LANG=en_US.UTF-8 pbcopy && osascript -e \\'display notification "Copied {{emoji}} to the clipboard" with title "Flashlight"\\'';
            flashlight.bash(command.replace(/{{emoji}}/g, emoji));
        }
    </script>
    <body class="{{appearance}}">
        <div class="message"></div>
        {{content}}
    </body>
    </html>
    """

    html = html.replace("{{appearance}}", appearance)
    return html.replace("{{content}}", content)


def build_emoji_html(emoji):
    html = """<div class="emoji"><i onclick="copyToClipboard('{{icon}}')">{{icon}}</i><label onclick="copyToClipboard('{{gemoji}}')">{{alias}}</label></div>"""

    alias = emoji['aliases'][0]
    gemoji = ':'+emoji['aliases'][0]+':'
    icon = emoji.get('emoji') or '-'

    html = html.replace('{{alias}}', alias)
    html = html.replace('{{gemoji}}', gemoji)
    return html.replace('{{icon}}', icon)


import json
def results(params, original_query):
    is_gemoji = False
    if params.has_key('~gemoji'):
        is_gemoji = True
        query = params['~gemoji']
    else:
        query = params['~emoji']

    emoji_arr = json.loads(open('emoji.json').read())

    emojis = find_emojis(query, emoji_arr)
    content = ''
    output = ''
    title = 'No emoji is matching your search'

    if len(emojis['matches']):
        output = emojis['matches'][0].get('emoji')
        title = "Press enter to insert the %s emoji" % (output)
        content = '<h1>Emojis matching your search <small>{} results</small></h1><div class="emojis">'.format(len(emojis['matches']))
        for emoji in emojis['matches']:
            content += build_emoji_html(emoji)
        content += '</div>'

    if len(emojis['others']):
        content += '<h1>Other emojis</h1><div class="emojis">'
        for emoji in emojis['others']:
            content += build_emoji_html(emoji)
        content += '</div>'

    return {
        'title': title,
        'run_args': [output] ,
        'html': build_html(appearance(), content),
        'webview_transparent_background': True,
    }


def run(output):
    import subprocess
    import os
    parent = os.fork()
    if parent > 0:
        return
    else:
        command = """tell application "System Events" to keystroke "" & (set the clipboard to "%s") & keystroke "v" using command down""" % (output)
        subprocess.call(["osascript", "-e", command])
        return


#print results({'~emoji': 'grin'}, 'emoji grinn')
#run(results({'~emoji': 'grin'}, 'emoji grinn')['run_args'][0])
