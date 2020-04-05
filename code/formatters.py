from talon import Module, Context, actions, ui
from typing import List, Union

ctx = Context()
key = actions.key

words_to_keep_lowercase = "a,an,the,at,by,for,in,is,of,on,to,up,and,as,but,or,nor".split(",")

def surround(by):
    def func(i, word, last):
        if i == 0:
            word = by + word
        if last:
            word += by
        return word

    return func

def FormatText(m, fmtrs):
    if m._words[-1] == "over":
        m._words = m._words[:-1]
    try:
        words = actions.dictate.parse_words(m)
        words = actions.dictate.replace_words(words)
    except AttributeError:
        with clip.capture() as s:
            edit.copy()
        words = s.get().split(" ")
        if not words:
            return
    
    return format_text_helper(words, fmtrs)

def format_text_helper(words, fmtrs):
    tmp = []
    spaces = True
    for i, w in enumerate(words):
        for name in reversed(fmtrs):
            smash, func = all_formatters[name]
            w = func(i, w, i == len(words) - 1)
            spaces = spaces and not smash
        tmp.append(w)
    words = tmp

    sep = " "
    if not spaces:
        sep = ""
    return sep.join(words)

NOSEP = True
SEP   = False

def words_with_joiner(joiner):
    """Pass through words unchanged, but add a separator between them."""
    def formatter_function(i, word, _):
        return word if i == 0 else joiner + word
    return (NOSEP, formatter_function)

def first_vs_rest(first_func, rest_func = lambda w: w):
    """Supply one or two transformer functions for the first and rest of
    words respectively.

    Leave second argument out if you want all but the first word to be passed
    through unchanged.
    Set first argument to None if you want the first word to be passed
    through unchanged."""
    if first_func is None:
        first_func = lambda w: w
    def formatter_function(i, word, _):
        return first_func(word) if i == 0 else rest_func(word)
    return formatter_function

def every_word(word_func):
    """Apply one function to every word."""
    def formatter_function(i, word, _):
        return word_func(word)
    return formatter_function

formatters_dict = {
    "DOUBLE_UNDERSCORE": (NOSEP, first_vs_rest(lambda w: "__%s__" % w)),
    "PRIVATE_CAMEL_CASE": (NOSEP, first_vs_rest(lambda w: w, lambda w: w.capitalize())),
    "PUBLIC_CAMEL_CASE": (NOSEP, every_word(lambda w: w.capitalize())),
    "SNAKE_CASE": (NOSEP, first_vs_rest(lambda w: w.lower(), lambda w: "_" + w.lower())),
    "NO_SPACES": (NOSEP, every_word(lambda w: w)),
    "DASH_SEPARATED": words_with_joiner("-"),
    "DOUBLE_COLON_SEPARATED": words_with_joiner("::"),
    "ALL_CAPS": (SEP, every_word(lambda w: w.upper())),
    "ALL_LOWERCASE": (SEP, every_word(lambda w: w.lower())),
    "DOUBLE_QUOTED_STRING": (SEP, surround('"')),
    "SINGLE_QUOTED_STRING": (SEP, surround("'")),
    "SPACE_SURROUNDED_STRING": (SEP, surround(" ")),
    "DOT_SEPARATED": words_with_joiner("."),
    "SLASH_SEPARATED": (NOSEP, every_word(lambda w: "/" + w)),
    "CAPITALIZE_FIRST_WORD": (SEP, first_vs_rest(lambda w: w.capitalize())),
    "CAPITALIZE_ALL_WORDS": (SEP, lambda i, word, _:  word.capitalize() if i == 0 or word not in words_to_keep_lowercase else word),
    "FIRST_THREE": (NOSEP, lambda i, word, _: word[0:3]),
    "FIRST_FOUR": (NOSEP, lambda i, word, _: word[0:4]),
    "FIRST_FIVE": (NOSEP, lambda i, word, _: word[0:5]),
}

# This is the mapping from spoken phrases to formatters
formatters_words = {
    "dunder": formatters_dict["DOUBLE_UNDERSCORE"],
    "camel": formatters_dict["PRIVATE_CAMEL_CASE"],
    "hammer": formatters_dict["PUBLIC_CAMEL_CASE"],
    "snake": formatters_dict["SNAKE_CASE"],
    "smash": formatters_dict["NO_SPACES"],
    "kebab": formatters_dict["DASH_SEPARATED"],
    "packed": formatters_dict["DOUBLE_COLON_SEPARATED"],
    "allcaps": formatters_dict["ALL_CAPS"],
    "alldown": formatters_dict["ALL_LOWERCASE"],
    "dubstring": formatters_dict["DOUBLE_QUOTED_STRING"],
    "string": formatters_dict["SINGLE_QUOTED_STRING"],
    "padded": formatters_dict["SPACE_SURROUNDED_STRING"],
    "dotted": formatters_dict["DOT_SEPARATED"],
    "slasher": formatters_dict["SLASH_SEPARATED"],
    "sentence": formatters_dict["CAPITALIZE_FIRST_WORD"],
    "title": formatters_dict["CAPITALIZE_ALL_WORDS"],
    "tree": formatters_dict["FIRST_THREE"],
    "quad": formatters_dict["FIRST_FOUR"],
    "fiver": formatters_dict["FIRST_FIVE"],
}

all_formatters = {}
all_formatters.update(formatters_dict)
all_formatters.update(formatters_words)

mod = Module()
mod.list('formatters', desc='list of formatters')

@mod.capture
def formatters(m) -> List[str]:
    "Returns a list of formatters"

@mod.capture
def format_text(m) -> str:
    "Formats the text and returns a string"

@mod.action_class
class Actions:
    def formatted_text(text: str, formatter: str) -> str:
        """Takes text and formats according to formatter"""
        return format_text_helper(text, [formatter])

    def formatters_format_text(text: Union[str, List[str]], fmtrs: List[str]) -> str:
        """Formats a list of parsed words given a list of formatters"""
        if isinstance(text, list):
            return format_text_helper(text, fmtrs)
        else:
            return format_text_helper([text], fmtrs)
        
@ctx.capture(rule='{self.formatters}+')
def formatters(m):
    return m.formatters_list
 
@ctx.capture(rule='<self.formatters> <phrase>')
def format_text(m):
    return FormatText(m.phrase, m.formatters)

ctx.lists['self.formatters'] = formatters_words.keys()
