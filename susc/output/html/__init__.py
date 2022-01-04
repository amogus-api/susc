from posixpath import dirname
from textwrap import indent
from typing import *
from susc import SusFile
from susc.things import *
from os import makedirs, path
from shutil import copy, copytree, rmtree
from susc import log
from colorama import Fore
from markdown import markdown

LICENSE = """
\tCopyright © 2021 portasynthinca3

\tPermission is hereby granted, free of charge, to any person obtaining a copy of this software and
\tassociated documentation files (the “Software”), to deal in the Software without restriction,
\tincluding without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
\tand/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
\tsubject to the following conditions:

\tThe above copyright notice and this permission notice shall be included in all copies or substantial
\tportions of the Software.

\tTHE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
\tLIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
\tNO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
\tWHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
\tSOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""

def write_output(root_file: SusFile, target_dir: str) -> None:
    proj_name = path.splitext(path.basename(root_file.path))[0]
    header = ("<!--\n\tGenerated by AMOGUS SUS (https://github.com/portasynthinca3/amogus)\n"
    f"\tProject name: {proj_name}\n\n"
    "" + LICENSE + "\n-->\n\n")

    # copy static presets
    copytree(path.join(dirname(__file__), "static"), path.join(target_dir, "static"))

    # copy topbar logo
    try:
        if "html_topbar_logo" in root_file.settings:
            topbar_logo = root_file.settings["html_topbar_logo"]
        else:
            log.info(f"Use {Fore.GREEN}'set html_topbar_logo <path>'{Fore.WHITE} to override the default topbar logo")
            topbar_logo = path.join(dirname(__file__), "topbar_default.png")
        copy(topbar_logo, path.join(target_dir, "topbar.png"))
    except:
        log.warn("Failed to copy topbar logo")

    if "html_topbar_title" in root_file.settings:
        topbar_title = root_file.settings["html_topbar_title"]
    else:
        log.info(f"Use {Fore.GREEN}'set html_topbar_title <path>'{Fore.WHITE} to override the default title")
        topbar_title = proj_name

    things = root_file.things

    log.verbose("Writing index.html")
    with open(path.join(target_dir, "index.html"), "w") as f:
        f.write(header)
        f.write("<html>\n")

        # head
        f.write("\t<head>\n")
        f.write(f"\t\t<title>{topbar_title} - Index</title>\n")
        f.write("\t\t<link rel='stylesheet' href='static/style.css'>\n")
        f.write("\t</head>\n")
        f.write("\t<body>\n")

        # topbar
        f.write("\t\t<div id='topbar'>\n")
        f.write("\t\t\t<img src='topbar.png' width='48' height='48'>\n")
        f.write(f"\t\t\t<a href='index.html'>{topbar_title}</a>\n")
        f.write("\t\t</div>\n")

        # thing lists
        enums = sorted([t for t in things if isinstance(t, SusEnum)], key=lambda t: t.name)
        methods = sorted([t for t in things if isinstance(t, SusMethod)], key=lambda t: t.name)
        entities = sorted([t for t in things if isinstance(t, SusEntity)], key=lambda t: t.name)
        bitfields = sorted([t for t in things if isinstance(t, SusBitfield)], key=lambda t: t.name)
        confirmations = sorted([t for t in things if isinstance(t, SusConfirmation)], key=lambda t: t.name)
        write_index_list(f, "Enums", "enum", enums)
        write_index_list(f, "Bitfields", "bf", bitfields)
        write_index_list(f, "Entities", "entity", entities)
        write_index_list(f, "Global methods", "gm", methods)
        write_index_list(f, "Confirmations", "conf", confirmations)

        # closing
        f.write("\t</body>\n")
        f.write("</html>\n")

    # create a page for each thing
    for thing in things:
        title, prefix = {
            SusEnum: ("enum", "enum_"),
            SusBitfield: ("bitfield", "bf_"),
            SusEntity: ("entity", "entity_"),
            SusMethod: ("global method", "gm_"),
            SusConfirmation: ("confirmation", "conf_")
        }[type(thing)]

        file_name = prefix + thing.name.lower() + ".html"
        log.verbose(f"Writing {file_name}")
        with open(path.join(target_dir, file_name), "w") as f:
            f.write(header)
            f.write("<html>\n")

            # head
            f.write("\t<head>\n")
            f.write(f"\t\t<title>{topbar_title} - {thing.name} {title}</title>\n")
            f.write("\t\t<link rel='stylesheet' href='static/style.css'>\n")
            f.write("\t</head>\n")
            f.write("\t<body>\n")

            # topbar
            f.write("\t\t<div id='topbar'>\n")
            f.write("\t\t\t<img src='topbar.png' width='48' height='48'>\n")
            f.write(f"\t\t\t<a href='index.html'>{topbar_title} <span><code>{thing.name}</code> {title}</span></a>\n")
            f.write("\t\t</div>\n")

            write_thing(f, thing)

            # closing
            f.write("\t</body>\n")
            f.write("</html>\n")


def format_docstring(docstr, indentation=2):
    if docstr is None:
        return ""
    docstr = docstr.replace("\n", "\n\n")
    return indent(f"<div class='docstring'>\n{markdown(docstr)}\n</div>\n", "\t" * indentation)
def format_type(type_: SusType):
    args = type_.args
    for i, arg in enumerate(args):
        if isinstance(arg, int):
            args[i] = str(arg)
        elif isinstance(arg, SusType):
            args[i] = format_type(arg)
    return type_.name + "(" + ", ".join(args) + ")"

def write_field(f, field: SusField, title: str, css_class: str):
    f.write("\t\t<div class='thing-member'>\n")
    f.write(f"\t\t\t<h3>{title}: <code class='{css_class}'>{field.name}</code></h3>\n")
    f.write(format_docstring(field.docstring, indentation=3))
    f.write(f"\t\t\t<div class='thing-param'>Type: <code>{format_type(field.type_)}</code></div>\n")
    if field.caching:
        f.write(f"\t\t\t<div class='thing-param'>Caching: {field.caching}</div>\n")
    if field.optional is not None:
        f.write(f"\t\t\t<div class='thing-param'>Optional ID: {field.optional}</div>\n")
    if field.default is not None:
        f.write(f"\t\t\t<div class='thing-param'>Default value: <code>{field.default}</code></div>\n")
    f.write("\t\t</div>\n")

def transform_cond_list(l):
    return ", ".join(f"<code class='field'>{m}</code>" for m in l)
def write_method(f, method: SusMethod, write_header=True):
    if write_header:
        f.write("\t\t<div class='thing-member'>\n")
    value_elm = "div" if write_header else "h3"
    if write_header:
        f.write(f"\t\t\t<h3>{'static ' if method.static else ''}method: <code class='method'>{method.name}</code></h3>\n")
    f.write(format_docstring(method.docstring, indentation=3))

    f.write(f"\t\t\t<{value_elm} class='thing-param'>Value: {method.value}</{value_elm}>\n")
    if method.errors:
        f.write(f"\t\t\t<{value_elm} class='thing-param'>Errors: {transform_cond_list(method.errors)}</{value_elm}>\n")
    if method.states:
        f.write(f"\t\t\t<{value_elm} class='thing-param'>States: {transform_cond_list(method.states)}</{value_elm}>\n")
    if method.confirmations:
        f.write(f"\t\t\t<{value_elm} class='thing-param'>Confirmations: {transform_cond_list(method.confirmations)}</{value_elm}>\n")

    for param in method.parameters:
        write_field(f, param, "parameter", "param")
    for param in method.returns:
        write_field(f, param, "return value", "ret-val")

    if write_header:
        f.write("\t\t</div>\n")

def write_thing(f, thing: SusThing):
    if isinstance(thing, (SusEnum, SusBitfield)):
        f.write(format_docstring(thing.docstring))
        f.write(f"\t\t<h3 class='thing-param'>Size: {thing.size} bytes ({thing.size * 8} bits)</h3>\n")

        for field in sorted(thing.members, key=lambda m: m.value):
            f.write("\t\t<div class='thing-member'>\n")
            f.write(f"\t\t\t<h3>member: <code class='field'>{field.name}</code></h3>\n")
            f.write(format_docstring(field.docstring, indentation=3))
            f.write(f"\t\t\t<div class='thing-param'>Value: {field.value}</div>\n")
            f.write("\t\t</div>\n")
    
    elif isinstance(thing, SusEntity):
        f.write(format_docstring(thing.docstring))
        f.write(f"\t\t<h3 class='thing-param'>Value: {thing.value}</h3>\n")
        for field in thing.fields:
            write_field(f, field, "field", "field")
        for method in thing.methods:
            write_method(f, method)
    
    elif isinstance(thing, SusConfirmation):
        f.write(format_docstring(thing.docstring))
        f.write(f"\t\t<h3 class='thing-param'>Value: {thing.value}</h3>\n")
        for param in thing.req_parameters:
            write_field(f, param, "request parameter", "param")
        for param in thing.resp_parameters:
            write_field(f, param, "response parameter", "ret-val")

    elif isinstance(thing, SusMethod):
        write_method(f, thing, False)

def correct_noun_form(amt, text):
    if amt == 1:
        return str(amt) + " " + text
    else:
        return str(amt) + " " + text + "s"
def noun_list(lst):
    return ", ".join([correct_noun_form(amt, noun) for amt, noun in lst if amt > 0])
def write_index_list(f, title, href_pref, elements):
    if len(elements) == 0:
        return
    f.write("\t\t<ul class='index-section'>\n")
    f.write(f"\t\t\t<h1>{title}</h1>\n")

    for elm in elements:
        info = ""
        if isinstance(elm, (SusEnum, SusBitfield)):
            info = noun_list([
                (len(elm.members), "member")
            ])
        if isinstance(elm, SusConfirmation):
            info = noun_list([
                (len(elm.req_parameters), "req. parameter"),
                (len(elm.resp_parameters), "resp. parameter")
            ])
        if isinstance(elm, SusMethod):
            info = noun_list([
                (len(elm.parameters), "parameter"),
                (len(elm.returns), "return value")
            ])
        if isinstance(elm, SusEntity):
            static = [m for m in elm.methods if m.static]
            normal = [m for m in elm.methods if not m.static]
            info = noun_list([
                (len(elm.fields), "field"),
                (len(static), "static method"),
                (len(normal), "dynamic method")
            ])
        if len(info) > 0:
            info = "(" + info + ")"

        f.write(f"\t\t\t<li><a href='{href_pref}_{elm.name.lower()}.html'>{elm.name}</a><span>{info}</span></li>\n")

    f.write("\t\t</ul>\n")