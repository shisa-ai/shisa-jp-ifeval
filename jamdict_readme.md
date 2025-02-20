Jamdict

Jamdict is a Python 3 library for manipulating Jim Breen's JMdict, KanjiDic2, JMnedict and kanji-radical mappings.

ReadTheDocs Badge

Documentation: https://jamdict.readthedocs.io/
Main features

    Support querying different Japanese language resources
        Japanese-English dictionary JMDict
        Kanji dictionary KanjiDic2
        Kanji-radical and radical-kanji maps KRADFILE/RADKFILE
        Japanese Proper Names Dictionary (JMnedict)
    Fast look up (dictionaries are stored in SQLite databases)
    Command-line lookup tool (Example)

Contributors are welcome! 🙇. If you want to help, please see Contributing page.
Try Jamdict out

Jamdict is used in Jamdict-web - a web-based free and open-source Japanese reading assistant software. Please try out the demo instance online at:

https://jamdict.herokuapp.com/

There also is a demo Jamdict virtual machine online for trying out Jamdict Python code on Repl.it:

https://replit.com/@tuananhle/jamdict-demo
Installation

Jamdict & Jamdict database are both available on PyPI and can be installed using pip

pip install --upgrade jamdict jamdict-data

Sample jamdict Python code

from jamdict import Jamdict
jam = Jamdict()

# use wildcard matching to find anything starts with 食べ and ends with る
result = jam.lookup('食べ%る')

# print all word entries
for entry in result.entries:
     print(entry)

# [id#1358280] たべる (食べる) : 1. to eat ((Ichidan verb|transitive verb)) 2. to live on (e.g. a salary)/to live off/to subsist on
# [id#1358300] たべすぎる (食べ過ぎる) : to overeat ((Ichidan verb|transitive verb))
# [id#1852290] たべつける (食べ付ける) : to be used to eating ((Ichidan verb|transitive verb))
# [id#2145280] たべはじめる (食べ始める) : to start eating ((Ichidan verb))
# [id#2449430] たべかける (食べ掛ける) : to start eating ((Ichidan verb))
# [id#2671010] たべなれる (食べ慣れる) : to be used to eating/to become used to eating/to be accustomed to eating/to acquire a taste for ((Ichidan verb))
# [id#2765050] たべられる (食べられる) : 1. to be able to eat ((Ichidan verb|intransitive verb)) 2. to be edible/to be good to eat ((pre-noun adjectival (rentaishi)))
# [id#2795790] たべくらべる (食べ比べる) : to taste and compare several dishes (or foods) of the same type ((Ichidan verb|transitive verb))
# [id#2807470] たべあわせる (食べ合わせる) : to eat together (various foods) ((Ichidan verb))

# print all related characters
for c in result.chars:
    print(repr(c))

# 食:9:eat,food
# 喰:12:eat,drink,receive (a blow),(kokuji)
# 過:12:overdo,exceed,go beyond,error
# 付:5:adhere,attach,refer to,append
# 始:8:commence,begin
# 掛:11:hang,suspend,depend,arrive at,tax,pour
# 慣:14:accustomed,get used to,become experienced
# 比:4:compare,race,ratio,Philippines
# 合:6:fit,suit,join,0.1

Command line tools

To make sure that jamdict is configured properly, try to look up a word using command line

python3 -m jamdict lookup 言語学
========================================
Found entries
========================================
Entry: 1264430 | Kj:  言語学 | Kn: げんごがく
--------------------
1. linguistics ((noun (common) (futsuumeishi)))

========================================
Found characters
========================================
Char: 言 | Strokes: 7
--------------------
Readings: yan2, eon, 언, Ngôn, Ngân, ゲン, ゴン, い.う, こと
Meanings: say, word
Char: 語 | Strokes: 14
--------------------
Readings: yu3, yu4, eo, 어, Ngữ, Ngứ, ゴ, かた.る, かた.らう
Meanings: word, speech, language
Char: 学 | Strokes: 8
--------------------
Readings: xue2, hag, 학, Học, ガク, まな.ぶ
Meanings: study, learning, science

No name was found.

Using KRAD/RADK mapping

Jamdict has built-in support for KRAD/RADK (i.e. kanji-radical and radical-kanji mapping). The terminology of radicals/components used by Jamdict can be different from else where.

    A radical in Jamdict is a principal component, each character has only one radical.
    A character may be decomposed into several writing components.

By default jamdict provides two maps:

    jam.krad is a Python dict that maps characters to list of components.
    jam.radk is a Python dict that maps each available components to a list of characters.

# Find all writing components (often called "radicals") of the character 雲
print(jam.krad['雲'])
# ['一', '雨', '二', '厶']

# Find all characters with the component 鼎
chars = jam.radk['鼎']
print(chars)
# {'鼏', '鼒', '鼐', '鼎', '鼑'}

# look up the characters info
result = jam.lookup(''.join(chars))
for c in result.chars:
    print(c, c.meanings())
# 鼏 ['cover of tripod cauldron']
# 鼒 ['large tripod cauldron with small']
# 鼐 ['incense tripod']
# 鼎 ['three legged kettle']
# 鼑 []

Finding name entities

# Find all names with 鈴木 inside
result = jam.lookup('%鈴木%')
for name in result.names:
    print(name)

# [id#5025685] キューティーすずき (キューティー鈴木) : Kyu-ti- Suzuki (1969.10-) (full name of a particular person)
# [id#5064867] パパイヤすずき (パパイヤ鈴木) : Papaiya Suzuki (full name of a particular person)
# [id#5089076] ラジカルすずき (ラジカル鈴木) : Rajikaru Suzuki (full name of a particular person)
# [id#5259356] きつねざきすずきひなた (狐崎鈴木日向) : Kitsunezakisuzukihinata (place name)
# [id#5379158] こすずき (小鈴木) : Kosuzuki (family or surname)
# [id#5398812] かみすずき (上鈴木) : Kamisuzuki (family or surname)
# [id#5465787] かわすずき (川鈴木) : Kawasuzuki (family or surname)
# [id#5499409] おおすずき (大鈴木) : Oosuzuki (family or surname)
# [id#5711308] すすき (鈴木) : Susuki (family or surname)
# ...

Exact matching

Use exact matching for faster search.

Find the word 花火 by idseq (1194580)

>>> result = jam.lookup('id#1194580')
>>> print(result.names[0])
[id#1194580] はなび (花火) : fireworks ((noun (common) (futsuumeishi)))

Find an exact name 花火 by idseq (5170462)

>>> result = jam.lookup('id#5170462')
>>> print(result.names[0])
[id#5170462] はなび (花火) : Hanabi (female given name or forename)

See jamdict_demo.py and jamdict/tools.py for more information.